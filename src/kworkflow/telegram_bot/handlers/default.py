from aiogram import F, Router, types
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from dishka.integrations.aiogram import FromDishka, inject

from kworkflow.auth.telegram_auth import TelegramAuth
from kworkflow.preferences.services import UserCategoryFollowService
from kworkflow.telegram_bot.keyboards import (
    MainMenuCB,
    build_main_menu_kbd,
    build_start_kbd,
)
from kworkflow.telegram_bot.messages import menu_message, start_message
from kworkflow.users.dto import CurrentUser

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
    current_user: FromDishka[CurrentUser],
    state: FSMContext,
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
        keyboard = build_main_menu_kbd(is_pro=current_user.is_pro)
    await message.answer(
        text,
        reply_markup=keyboard,
    )
    await state.clear()


@router.message(F.text, Command("menu"))
@inject
async def main_menu_command_handler(
    message: types.Message,
    service: FromDishka[UserCategoryFollowService],
    current_user: FromDishka[CurrentUser],
    state: FSMContext,
):
    categories = await service.get_followed_categories()
    text = menu_message(categories)
    keyboard = build_main_menu_kbd(is_pro=current_user.is_pro)
    await message.answer(text, reply_markup=keyboard)
    await state.clear()


@router.callback_query(MainMenuCB.filter())
@inject
async def main_menu_cb_handler(
    call: types.CallbackQuery,
    service: FromDishka[UserCategoryFollowService],
    current_user: FromDishka[CurrentUser],
    state: FSMContext,
    callback_data: MainMenuCB,
):
    categories = await service.get_followed_categories()
    text = menu_message(categories)
    keyboard = build_main_menu_kbd(is_pro=current_user.is_pro)
    if callback_data.delete_message:
        await call.message.delete()
    await call.message.answer(text, reply_markup=keyboard)
    await state.clear()
    await call.answer()
