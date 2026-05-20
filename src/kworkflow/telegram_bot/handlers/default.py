from aiogram import F, Router, types
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from dishka.integrations.aiogram import FromDishka, inject

from kworkflow.auth.telegram_auth import TelegramAuth
from kworkflow.telegram_bot.keyboards import build_start_kbd

router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(
    F.message.chat.type == ChatType.PRIVATE,
)


@router.message(CommandStart())
@inject
async def start_handler(
    message: types.Message,
    auth: FromDishka[TelegramAuth],
):
    if message.from_user is None:
        return
    await auth.auth()
    keyboard = build_start_kbd()
    await message.answer(
        "👋 Добро пожаловать в <b>KworkFlow</b>\n\n"
        "Мониторю проекты на бирже Kwork и присылаю новые мгновенно.\n\n"
        "⚡ Что я делаю:\n"
        "• Мониторинг новых проектов\n"
        "• Мгновенные уведомления\n"
        "• Генерация автоматических откликов\n\n"
        "📂 Настрой категории — и я начну мониторинг",
        reply_markup=keyboard,
    )
