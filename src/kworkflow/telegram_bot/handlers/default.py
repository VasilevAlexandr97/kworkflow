from aiogram import F, Router, types
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from dishka.integrations.aiogram import FromDishka, inject

from kworkflow.auth.telegram_auth import TelegramAuth
from kworkflow.preferences.services import UserCategoryFollowService
from kworkflow.telegram_bot.keyboards import build_menu_kbd, build_start_kbd
from kworkflow.telegram_bot.messages import menu_message, start_message

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
    service: FromDishka[UserCategoryFollowService],
):
    if message.from_user is None:
        return
    result = await auth.auth()
    if result.is_new:
        text = start_message()
        keyboard = build_start_kbd()
    else:
        categories = await service.get_followed_categories()
        text = menu_message(categories)
        keyboard = build_menu_kbd()
    await message.answer(
        text,
        reply_markup=keyboard,
    )


@router.message(F.text, Command("menu"))
@inject
async def menu_handler(
    message: types.Message,
    service: FromDishka[UserCategoryFollowService],
):
    categories = await service.get_followed_categories()
    text = menu_message(categories)
    keyboard = build_menu_kbd()
    await message.answer(text, reply_markup=keyboard)
