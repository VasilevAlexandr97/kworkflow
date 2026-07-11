import contextlib

from aiogram import Bot, F, Router, types
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from dishka.integrations.aiogram import FromDishka, inject

from kworkflow.preferences.exceptions import (
    UserCategoryFollowLimitExceededError,
)
from kworkflow.preferences.services import (
    UserCategoryFollowService,
    UserFreelancerProfileService,
    UserStopWordsService,
)
from kworkflow.projects.services import ProjectCategoryService
from kworkflow.telegram_bot.keyboards import (
    ManageAction,
    ManageFollowedCategoriesCB,
    build_edit_profile_kbd,
    build_followed_categories_kbd,
    build_followed_subcategories_kbd,
    build_profile_menu_kbd,
    build_start_add_stop_words_kbd,
    build_start_delete_stop_words_kbd,
    build_stop_words_menu_kbd,
)
from kworkflow.telegram_bot.messages import (
    categories_limit_exceeded_message,
    empty_stop_words_delete_message,
    profile_info_message,
    profile_not_set_message,
    select_followed_categories_message,
    start_add_stop_words_message,
    start_delete_stop_words_message,
    start_edit_profile_message,
    stop_words_limit_exceeded_message,
    stop_words_menu_message,
    unfollow_all_categories_message,
)
from kworkflow.telegram_bot.states import (
    FreelancerProfileState,
    StopWordsState,
)

router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(
    F.message.chat.type == ChatType.PRIVATE,
)


@router.callback_query(F.data == "configure_followed_categories")
@router.callback_query(
    ManageFollowedCategoriesCB.filter(
        F.action == ManageAction.BROWSE_CATEGORIES,
    ),
)
@inject
async def start_configure_followed_categories(
    call: types.CallbackQuery,
    service: FromDishka[ProjectCategoryService],
):
    root_categories = await service.get_root_categories()
    if not root_categories:
        pass
    text = select_followed_categories_message()
    keyboard = build_followed_categories_kbd(root_categories)
    await call.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(
    ManageFollowedCategoriesCB.filter(
        F.action == ManageAction.BROWSE_SUBCATEGORIES,
    ),
    ManageFollowedCategoriesCB.filter(
        F.category_id.is_not(None),
    ),
)
@inject
async def browse_followed_subcategories(
    call: types.CallbackQuery,
    service: FromDishka[UserCategoryFollowService],
    callback_data: ManageFollowedCategoriesCB,
):
    categories = await service.get_subcategories_with_follow_status(
        parent_id=callback_data.category_id,
    )
    text = select_followed_categories_message()
    keyboard = build_followed_subcategories_kbd(categories)
    await call.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(
    ManageFollowedCategoriesCB.filter(F.action == ManageAction.FOLLOW),
    ManageFollowedCategoriesCB.filter(F.category_id.is_not(None)),
)
@router.callback_query(
    ManageFollowedCategoriesCB.filter(F.action == ManageAction.UNFOLLOW),
    ManageFollowedCategoriesCB.filter(F.category_id.is_not(None)),
)
@inject
async def follow_category(
    call: types.CallbackQuery,
    service: FromDishka[UserCategoryFollowService],
    callback_data: ManageFollowedCategoriesCB,
):
    if not callback_data.category_id:
        return
    try:
        result = await service.toggle_category_follow(
            callback_data.category_id,
        )
        text = select_followed_categories_message()
        keyboard = build_followed_subcategories_kbd(result.categories)
        await call.message.edit_text(text, reply_markup=keyboard)
    except UserCategoryFollowLimitExceededError as exc:
        text = categories_limit_exceeded_message(exc.limit)
        await call.answer(text, show_alert=True)


@router.callback_query(
    ManageFollowedCategoriesCB.filter(F.action == ManageAction.UNFOLLOW_ALL),
)
@inject
async def unfollow_all_categories(
    call: types.CallbackQuery,
    service: FromDishka[UserCategoryFollowService],
    state: FSMContext,
):
    await service.unfollow_all_categories()
    text = unfollow_all_categories_message()
    await call.answer(text, show_alert=True)
    await state.clear()


@router.callback_query(F.data == "profile")
@router.callback_query(F.data == "cancel_edit_profile")
@inject
async def profile_menu(
    call: types.CallbackQuery,
    service: FromDishka[UserFreelancerProfileService],
    state: FSMContext,
):
    profile = await service.get_profile()
    if profile and profile.about:
        text = profile_info_message(profile.about)
    else:
        text = profile_not_set_message()
    keyboard = build_profile_menu_kbd()
    await call.message.edit_text(text, reply_markup=keyboard)
    await state.clear()


@router.callback_query(F.data == "edit_profile")
@inject
async def start_edit_profile(
    call: types.CallbackQuery,
    state: FSMContext,
):
    text = start_edit_profile_message()
    keyboard = build_edit_profile_kbd()
    await state.set_data({"last_message_id": call.message.message_id})
    await state.set_state(FreelancerProfileState.edit)
    await call.message.edit_text(text, reply_markup=keyboard)


@router.message(FreelancerProfileState.edit, F.text)
@inject
async def edit_profile(
    message: types.Message,
    service: FromDishka[UserFreelancerProfileService],
    bot: FromDishka[Bot],
    state: FSMContext,
):
    if not message.text:
        return
    state_data = await state.get_data()
    last_message_id = state_data.get("last_message_id")
    profile_text = message.text
    profile = await service.edit_or_create_profile(profile_text)
    if profile and profile.about:
        text = profile_info_message(profile.about)
    else:
        text = profile_not_set_message()
    keyboard = build_profile_menu_kbd()
    await message.answer(text, reply_markup=keyboard)
    try:
        if last_message_id:
            await bot.delete_message(message.from_user.id, last_message_id)
    except TelegramBadRequest:
        pass
    await state.clear()


@router.callback_query(F.data == "stop_words_menu")
@router.callback_query(F.data == "cancel_add_stop_words")
@router.callback_query(F.data == "cancel_delete_stop_words")
@inject
async def stop_words_menu(
    call: types.CallbackQuery,
    service: FromDishka[UserStopWordsService],
    state: FSMContext,
):
    result = await service.get_stop_words()
    text = stop_words_menu_message(words=result.words, limit=result.limit)
    keyboard = build_stop_words_menu_kbd()
    await call.message.edit_text(text, reply_markup=keyboard)
    await state.clear()


@router.callback_query(F.data == "add_stop_words")
@inject
async def start_add_stop_words(
    call: types.CallbackQuery,
    service: FromDishka[UserStopWordsService],
    state: FSMContext,
):
    result = await service.count_stop_words()
    if result.count >= result.limit:
        text = stop_words_limit_exceeded_message(result.limit)
        await call.answer(text, show_alert=True)
    else:
        text = start_add_stop_words_message()
        keyboard = build_start_add_stop_words_kbd()
        await state.set_data({"last_message_id": call.message.message_id})
        await state.set_state(StopWordsState.add)
        await call.message.edit_text(text, reply_markup=keyboard)


@router.message(StopWordsState.add)
@inject
async def add_stop_words(
    message: types.Message,
    service: FromDishka[UserStopWordsService],
    state: FSMContext,
    bot: FromDishka[Bot],
):
    state_data = await state.get_data()
    last_message_id = state_data.get("last_message_id")
    stop_words = message.text.split(",")
    result = await service.add_stop_words(stop_words)
    text = stop_words_menu_message(words=result.words, limit=result.limit)
    keyboard = build_stop_words_menu_kbd()
    if last_message_id is not None:
        with contextlib.suppress(TelegramBadRequest):
            await bot.delete_message(message.from_user.id, last_message_id)
    await message.answer(text, reply_markup=keyboard)
    await state.clear()


@router.callback_query(F.data == "delete_stop_words")
@inject
async def start_delete_stop_words(
    call: types.CallbackQuery,
    service: FromDishka[UserStopWordsService],
    state: FSMContext,
):
    result = await service.get_stop_words()
    if not result.words:
        text = empty_stop_words_delete_message()
        await call.answer(text, show_alert=True)
    else:
        text = start_delete_stop_words_message(result.words)
        keyboard = build_start_delete_stop_words_kbd()
        await state.set_data({"last_message_id": call.message.message_id})
        await state.set_state(StopWordsState.delete)
        await call.message.edit_text(text, reply_markup=keyboard)


@router.message(StopWordsState.delete)
@inject
async def delete_stop_words(
    message: types.Message,
    service: FromDishka[UserStopWordsService],
    state: FSMContext,
    bot: FromDishka[Bot],
):
    state_data = await state.get_data()
    last_message_id = state_data.get("last_message_id")
    stop_words = message.text.split(",")
    result = await service.delete_stop_words(stop_words)
    text = stop_words_menu_message(words=result.words, limit=result.limit)
    keyboard = build_stop_words_menu_kbd()
    if last_message_id is not None:
        with contextlib.suppress(TelegramBadRequest):
            await bot.delete_message(message.from_user.id, last_message_id)
    await message.answer(text, reply_markup=keyboard)
    await state.clear()
