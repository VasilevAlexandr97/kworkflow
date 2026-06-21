import logging

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid7

from kworkflow.auth.exceptions import AuthenticationError
from kworkflow.auth.id_provider import IdProvider
from kworkflow.infra.database.transaction_manager import TransactionManager
from kworkflow.users.exceptions import CreateUserError, UserAlreadyExistsError
from kworkflow.users.gateways import UserGateway
from kworkflow.users.models import User

logger = logging.getLogger(__name__)


@dataclass
class TelegramAuthResultDTO:
    user_id: UUID
    is_new: bool


class TelegramAuth:
    def __init__(
        self,
        user_gateway: UserGateway,
        id_provider: IdProvider,
        transaction_manager: TransactionManager,
    ):
        self.user_gateway = user_gateway
        self.id_provider = id_provider
        self.transaction_manager = transaction_manager

    async def auth(
        self,
    ) -> TelegramAuthResultDTO:
        try:
            user_id = await self.id_provider.get_current_user_id()
            return TelegramAuthResultDTO(user_id=user_id, is_new=False)
        except AuthenticationError:
            pass
        new_id = uuid7()
        telegram_id = await self.id_provider.get_current_user_telegram_id()
        now = datetime.now(tz=UTC)
        new_user = User(
            id=new_id,
            telegram_id=telegram_id,
            created_at=now,
            updated_at=now,
        )
        try:
            await self.user_gateway.add(new_user)
            await self.transaction_manager.commit()
        except UserAlreadyExistsError:
            await self.transaction_manager.rollback()
            logger.info(f"User already exists: {new_user!r}")
            user = await self.user_gateway.get_by_telegram_id(telegram_id)
            if user is None:
                raise CreateUserError
            return TelegramAuthResultDTO(user_id=user.id, is_new=False)
        except CreateUserError:
            await self.transaction_manager.rollback()
            logger.info(f"User not created: {new_user!r}")
            raise
        return TelegramAuthResultDTO(user_id=new_id, is_new=True)
