import logging

from base64 import b64encode
from datetime import datetime
from enum import StrEnum
from uuid import uuid4

import httpx

from pydantic import BaseModel, Field

from kworkflow.common.interfaces.limiter import RateLimiter

logger = logging.getLogger(__name__)


class Currency(StrEnum):
    RUB = "RUB"


class ConfirmationType(StrEnum):
    REDIRECT = "redirect"


class AmountData(BaseModel):
    value: str
    currency: str | Currency


class CustomerData(BaseModel):
    full_name: str | None = None
    inn: str | None = None
    email: str | None = None
    phone: str | None = None


class ReceiptItemData(BaseModel):
    description: str
    amount: AmountData
    vat_code: int = Field(default=1, ge=1, le=12)
    quantity: float = 1.0


class ConfirmationRedirectData(BaseModel):
    type: str | ConfirmationType
    return_url: str | None = None
    confirmation_url: str | None = None


class ReceiptData(BaseModel):
    customer: CustomerData | None
    items: list[ReceiptItemData]


class PaymentRequest(BaseModel):
    amount: AmountData
    description: str | None = None
    receipt: ReceiptData | None = None
    payment_method_id: str | None = None
    confirmation: ConfirmationRedirectData | None = None
    save_payment_method: bool = True
    capture: bool = True
    metadata: dict | None = None


class Status(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"


class RecipientData(BaseModel):
    account_id: str
    gateway_id: str


class PaymentMethodData(BaseModel):
    type: str
    id: str
    saved: bool
    status: str


class CancellationDetailsData(BaseModel):
    party: str
    reason: str


class PaymentResponse(BaseModel):
    id: str
    status: Status
    amount: AmountData
    description: str
    recipient: RecipientData
    created_at: datetime
    test: bool
    paid: bool
    refundable: bool
    payment_method: PaymentMethodData | None = None
    confirmation: ConfirmationRedirectData | None = None
    cancellation_details: CancellationDetailsData | None = None
    metadata: dict | None = None


class YooKassaClient:
    BASE_URL = "https://api.yookassa.ru/v3"

    def __init__(
        self,
        shop_id: str,
        secret_key: str,
        limiter: RateLimiter | None = None,
    ):
        self.limiter = limiter
        self._auth = b64encode(f"{shop_id}:{secret_key}".encode()).decode()
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Basic {self._auth}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def create_payment(
        self,
        payment_request: PaymentRequest,
    ) -> PaymentResponse:
        if self.limiter:
            await self.limiter.acquire()
        payload = payment_request.model_dump(exclude_none=True)
        logger.debug(f"PAYLOAD: {payload}")
        resp = await self._client.post(
            "/payments",
            json=payload,
            headers={"Idempotence-Key": str(uuid4())},
        )
        try:
            resp.raise_for_status()
            json_data = resp.json()
            logger.debug(f"RESPONSE JSON DATA: {json_data}")
            return PaymentResponse(**json_data)
        except httpx.HTTPStatusError:
            logger.debug(f"RESPONSE TEXT: {resp.text}")
            raise

    async def get_payment(self, payment_id: str) -> PaymentResponse:
        if self.limiter:
            await self.limiter.acquire()
        resp = await self._client.get(f"/payments/{payment_id}")
        try:
            resp.raise_for_status()
            json_data = resp.json()
            logger.info(f"JSON DATA: {json_data}")
            return PaymentResponse(**json_data)
        except httpx.HTTPStatusError:
            logger.debug(f"RESPONSE TEXT: {resp.text}")
            raise

    async def close(self):
        await self._client.aclose()
