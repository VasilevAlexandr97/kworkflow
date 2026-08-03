from datetime import UTC, datetime
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.methods import TelegramMethod
from aiogram.types import Chat, Message, Update, User


class FakeBot(Bot):
    def __init__(self):
        self.sent_methods: list[TelegramMethod[Any]] = []

    @property
    def id(self):
        return 1

    async def __call__(
        self,
        method: TelegramMethod[Any],
        request_timeout: int | None = None,
    ) -> Any:
        del request_timeout
        self.sent_methods.append(method)
        return True

    def __hash__(self) -> int:
        return 1

    def __eq__(self, other) -> bool:
        return self is other


class BotClient:
    def __init__(
        self,
        dp: Dispatcher,
        bot: FakeBot,
        user_id: int = 1,
        chat_id: int = 1,
    ):
        self.chat_id = chat_id
        self.user = User(
            id=user_id,
            is_bot=False,
            first_name=f"User_{user_id}",
        )
        self.dp = dp
        self.last_update_id = 1
        self.last_message_id = 1
        self.bot = bot

    def _new_update_id(self):
        self.last_update_id += 1
        return self.last_update_id

    def _new_message_id(self):
        self.last_message_id += 1
        return self.last_message_id

    def _new_chat(self, chat_type: ChatType | None = None) -> Chat:
        chat_type = chat_type or ChatType.PRIVATE
        return Chat(id=self.chat_id, type=chat_type)

    def _new_message(
        self,
        text: str,
        reply_to: Message | None,
        chat_type: ChatType | None = None,
        with_user: bool = True,
    ):
        user = self.user if with_user else None
        chat = self._new_chat(chat_type)
        return Message(
            message_id=self._new_message_id(),
            date=datetime.now(UTC),
            chat=chat,
            from_user=user,
            text=text,
            reply_to_message=reply_to,
        )

    async def send_message(
        self,
        text: str,
        reply_to: Message | None = None,
        chat_type: ChatType | None = None,
        with_user: bool = True,
        state: FSMContext | None = None,
    ):
        return await self.dp.feed_update(
            self.bot,
            Update(
                update_id=self._new_update_id(),
                message=self._new_message(
                    text=text,
                    reply_to=reply_to,
                    chat_type=chat_type,
                    with_user=with_user,
                ),
            ),
            state=state,
        )

    # def _new_callback(
    #     self,
    #     message: Message,
    #     button: InlineKeyboardButton,
    # ) -> CallbackQuery:
    #     if not button.callback_data:
    #         raise ValueError("Button has no callback data")
    #     return CallbackQuery(
    #         id=str(uuid.uuid4()),
    #         data=button.callback_data,
    #         chat_instance="--",
    #         from_user=self.user,
    #         message=message,
    #     )

    # async def click(
    #     self,
    #     message: Message,
    #     locator: InlineButtonLocator,
    # ) -> str:
    #     button = locator.find_button(message)
    #     if not button:
    #         raise ValueError(
    #             f"No button matching {locator} found",
    #         )

    #     callback = self._new_callback(message, button)
    #     await self.dp.feed_update(
    #         self.bot,
    #         Update(
    #             update_id=self._new_update_id(),
    #             callback_query=callback,
    #         ),
    #     )
    #     return callback.id
