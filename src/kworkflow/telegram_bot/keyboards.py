from enum import StrEnum
from uuid import UUID

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from kworkflow.projects.models import ProjectCategory


class CatAction(StrEnum):
    BROWSE = "browse"
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    UNFOLLOW_ALL = "unfollow_all"
    BACK = "back"
    CONFIRM = "confirm"


class CategoryCB(CallbackData, prefix="cat"):
    action: CatAction
    category_id: UUID | None = None


class GenerateProposalCB(CallbackData, prefix="gen_proposal"):
    project_id: UUID


class MainMenuCB(CallbackData, prefix="main_menu"):
    delete_message: bool = False


def build_start_kbd() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📂 Категории",
        callback_data=CategoryCB(action=CatAction.BROWSE).pack(),
    )
    return builder.as_markup()


def build_main_menu_kbd():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📂 Категории",
            callback_data=CategoryCB(action=CatAction.BROWSE).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🛑 Стоп слова",
            callback_data="stop_words_menu",
        ),
    )
    return builder.as_markup()


def build_follow_categories_kbd(
    categories: list[ProjectCategory],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=category.title,
                callback_data=CategoryCB(
                    action=CatAction.BROWSE,
                    category_id=category.id,
                ).pack(),
            ),
        )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отписаться от всех",
            callback_data=CategoryCB(
                action=CatAction.UNFOLLOW_ALL,
                category_id=None,
            ).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="💾 Сохранить",
            callback_data=CategoryCB(action=CatAction.CONFIRM).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🏚 Меню",
            callback_data=MainMenuCB(delete_message=True).pack(),
        ),
    )
    return builder.as_markup()


def build_follow_subcategories_kbd(
    categories: list[ProjectCategory],
    follow_category_ids: list[UUID],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        status = "✅" if category.id in follow_category_ids else "⬜️"
        action = (
            CatAction.FOLLOW
            if category.id not in follow_category_ids
            else CatAction.UNFOLLOW
        )
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {category.title}",
                callback_data=CategoryCB(
                    action=action,
                    category_id=category.id,
                ).pack(),
            ),
        )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=CategoryCB(action=CatAction.BACK).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="💾 Подтвердить",
            callback_data=CategoryCB(action=CatAction.CONFIRM).pack(),
        ),
    )
    return builder.as_markup()


def build_stop_words_menu_kbd():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить",
            callback_data="add_stop_words",
        ),
        InlineKeyboardButton(
            text="➖ Удалить",
            callback_data="delete_stop_words",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🏚 Меню",
            callback_data=MainMenuCB(delete_message=True).pack(),
        ),
    )
    return builder.as_markup()


def build_start_add_stop_words_kbd():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✖️ Отмена",
            callback_data="cancel_add_stop_words",
        ),
    )
    return builder.as_markup()


def build_start_delete_stop_words_kbd():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✖️ Отмена",
            callback_data="cancel_delete_stop_words",
        ),
    )
    return builder.as_markup()


def build_project_kbd(project_id: UUID):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✍️ Сгенерировать отклик",
            callback_data=GenerateProposalCB(project_id=project_id).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🏚 Меню",
            callback_data=MainMenuCB(delete_message=False).pack(),
        ),
    )
    return builder.as_markup()
