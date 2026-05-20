from uuid import UUID

from aiogram import F, Router, types
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from dishka.integrations.aiogram import FromDishka, inject

from kworkflow.preferences.services import UserCategoryFollowService
from kworkflow.projects.services import ProjectCategoryService
from kworkflow.telegram_bot.keyboards import (
    CatAction,
    CategoryCB,
    build_follow_categories_kbd,
    build_follow_subcategories_kbd,
    build_main_menu_kbd,
)

router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(
    F.message.chat.type == ChatType.PRIVATE,
)


@router.callback_query(
    CategoryCB.filter(
        F.action == CatAction.BROWSE,
    ),
    CategoryCB.filter(
        F.category_id.is_(None),
    ),
)
@inject
async def start_category_follow(
    call: types.CallbackQuery,
    service: FromDishka[UserCategoryFollowService],
    state: FSMContext,
):
    result = await service.get_categories_with_follow_status()
    root_categories = [
        r.category for r in result if r.category.parent_id is None
    ]
    follow_category_ids = [str(r.category.id) for r in result if r.is_followed]
    keyboard = build_follow_categories_kbd(root_categories)
    await state.set_data({"follow_category_ids": follow_category_ids})
    await call.message.answer("📂 Выберите Категории:", reply_markup=keyboard)
    await call.message.edit_reply_markup(reply_markup=None)


@router.callback_query(CategoryCB.filter(F.action == CatAction.BACK))
@inject
async def back_root_categories(
    call: types.CallbackQuery,
    service: FromDishka[ProjectCategoryService],
):
    categories = await service.get_root_categories()
    keyboard = build_follow_categories_kbd(categories)
    await call.message.edit_text(
        "📂 Выберите Категории:",
        reply_markup=keyboard,
    )


@router.callback_query(
    CategoryCB.filter(F.action == CatAction.BROWSE),
    CategoryCB.filter(F.category_id.is_not(None)),
)
@inject
async def show_follow_subcategories(
    call: types.CallbackQuery,
    callback_data: CategoryCB,
    service: FromDishka[ProjectCategoryService],
    state: FSMContext,
):
    if callback_data.category_id is None:
        return
    state_data = await state.get_data()
    categories = await service.get_subcategories(callback_data.category_id)
    follow_category_ids = [
        UUID(i) for i in state_data.get("follow_category_ids", [])
    ]
    state_data["root_id"] = str(callback_data.category_id)
    keyboard = build_follow_subcategories_kbd(
        categories,
        follow_category_ids,
    )
    await state.set_data(state_data)
    await call.message.edit_text(
        "📂 Выберите Категории:",
        reply_markup=keyboard,
    )


@router.callback_query(
    CategoryCB.filter(F.action == CatAction.FOLLOW),
    CategoryCB.filter(F.category_id.is_not(None)),
)
@router.callback_query(
    CategoryCB.filter(F.action == CatAction.UNFOLLOW),
    CategoryCB.filter(F.category_id.is_not(None)),
)
@inject
async def follow_category(
    call: types.CallbackQuery,
    callback_data: CategoryCB,
    service: FromDishka[ProjectCategoryService],
    state: FSMContext,
):
    state_data = await state.get_data()
    root_id = UUID(state_data.get("root_id"))
    categories = await service.get_subcategories(root_id)
    follow_category_ids: list = [
        UUID(i) for i in state_data.get("follow_category_ids", [])
    ]
    if callback_data.action == CatAction.FOLLOW:
        follow_category_ids.append(callback_data.category_id)
    else:
        follow_category_ids = [
            i for i in follow_category_ids if i != callback_data.category_id
        ]
    state_data["follow_category_ids"] = [str(i) for i in follow_category_ids]
    await state.set_data(state_data)
    keyboard = build_follow_subcategories_kbd(
        categories,
        follow_category_ids,
    )
    await call.message.edit_text(
        "📂 Выберите Категории:",
        reply_markup=keyboard,
    )


@router.callback_query(
    CategoryCB.filter(F.action == CatAction.CONFIRM),
)
@inject
async def save_category_follow(
    call: types.CallbackQuery,
    service: FromDishka[UserCategoryFollowService],
    state: FSMContext,
):
    state_data = await state.get_data()
    follow_category_ids = [
        UUID(i) for i in state_data.get("follow_category_ids", [])
    ]
    categories = await service.sync_user_follows(follow_category_ids)
    keyboard = build_main_menu_kbd()
    await state.clear()
    await call.message.edit_text(
        "✅ Настройка завершена.\n\n"
        "Выбранные категории:\n"
        f"{'\n'.join([f"- {c.title}" for c in categories])}\n\n"
        "Мониторинг активирован — уведомления о новых проектах будут приходить автоматически.",
        reply_markup=keyboard,
    )
