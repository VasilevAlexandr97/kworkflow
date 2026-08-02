import logging

from decimal import Decimal
from http import HTTPStatus
from typing import TypeVar

from openai import APIStatusError, AsyncOpenAI
from pydantic import BaseModel

from kworkflow.common.interfaces.limiter import RateLimiter
from kworkflow.common.interfaces.llm_client import (
    LLMClient,
    LLMClientError,
    LLMCompletion,
    LLMInsufficientBalanceError,
    LLMUsage,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

INSUFFICIENT_BALANCE_CODE = "INSUFFICIENT_BALANCE"


class PolzaClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://polza.ai/api/v1",
        limiter: RateLimiter | None = None,
    ):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.limiter = limiter

    def _extract_error(self, exc: APIStatusError) -> tuple[str, str] | None:
        body = exc.body
        if not isinstance(body, dict):
            return None
        code = body.get("code")
        if isinstance(code, str):
            message = body.get("message")
            return code, message if isinstance(message, str) else exc.message
        return None

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_format: type[T],
        max_tokens: int | None = None,
    ) -> LLMCompletion[T]:
        if self.limiter is not None:
            await self.limiter.acquire()
        try:
            completion = await self.client.chat.completions.parse(
                model="anthropic/claude-sonnet-4.6",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                response_format=response_format,
                max_tokens=max_tokens,
            )
        except APIStatusError as exc:
            if exc.status_code == HTTPStatus.PAYMENT_REQUIRED:
                code, message = self._extract_error(exc) or (None, exc.message)
                if code == INSUFFICIENT_BALANCE_CODE:
                    raise LLMInsufficientBalanceError(message) from exc
            logger.exception(
                f"Polza API error {exc.status_code}: {exc.body}",
            )
            raise LLMClientError(exc.message) from exc
        except Exception as exc:
            logger.exception("Polza LLM request failed")
            raise LLMClientError(f"LLM request failed: {exc}") from exc
        prompt_tokens = getattr(completion.usage, "prompt_tokens", 0)
        completion_tokens = getattr(completion.usage, "completion_tokens", 0)
        total_tokens = getattr(completion.usage, "total_tokens", 0)
        cost = Decimal(getattr(completion.usage, "cost_rub", 0))
        result = completion.choices[0].message.parsed
        if result is None:
            raise LLMClientError("LLM return None response")
        return LLMCompletion(
            parsed=result,
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost,
            ),
        )

    async def close(self) -> None:
        await self.client.close()
