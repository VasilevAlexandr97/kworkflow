import contextlib
import logging

from aiogram import F, Router, types
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from dishka.integrations.aiogram import FromDishka, inject

from kworkflow.main.config import Config
from kworkflow.subscriptions.exceptions import (
    PaymentEmailRequiredError,
    PaymentEmailValidationError,
)
from kworkflow.subscriptions.models import PlanSlug
from kworkflow.subscriptions.services import SubscriptionService
from kworkflow.telegram_bot.keyboards import (
    build_payment_email_kbd,
    build_payment_kbd,
    build_subscription_plan_kbd,
)
from kworkflow.telegram_bot.messages import (
    payment_email_message,
    payment_email_validation_error_message,
    payment_message,
    pro_subscription_info_message,
)
from kworkflow.telegram_bot.states import PaymentState

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(
    F.message.chat.type == ChatType.PRIVATE,
)


@router.callback_query(F.data == "pro_subscription")
@inject
async def pro_subscription_info(
    call: types.CallbackQuery,
    service: FromDishka[SubscriptionService],
):
    plan = await service.get_plan_for_user()
    text = pro_subscription_info_message(PlanSlug(plan.slug))
    keyboard = build_subscription_plan_kbd(
        slug=plan.slug,
        price=plan.price_rub,
    )
    await call.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "create_payment")
@inject
async def create_payment(
    call: types.CallbackQuery,
    service: FromDishka[SubscriptionService],
    state: FSMContext,
    config: FromDishka[Config],
):
    if not config.debug:
        await call.answer()
        return
    try:
        payment = await service.get_or_create_pending_payment()
        text = payment_message(
            payment_id=payment.yookassa_payment_id,
            email=payment.email,
            link=payment.link,
        )
        keyboard = build_payment_kbd(payment.link)
    except PaymentEmailRequiredError:
        text = payment_email_message()
        keyboard = build_payment_email_kbd()
        await state.set_state(PaymentState.set_email)
    with contextlib.suppress(TelegramBadRequest):
        await call.message.edit_text(text, reply_markup=keyboard)


@router.message(PaymentState.set_email)
@inject
async def set_payment_email(
    message: types.Message,
    service: FromDishka[SubscriptionService],
    state: FSMContext,
):
    state_clear = False
    try:
        email = message.text
        payment = await service.get_or_create_pending_payment(email)
        text = payment_message(
            payment_id=payment.yookassa_payment_id,
            email=payment.email,
            link=payment.link,
        )
        keyboard = build_payment_kbd(payment.link)
        state_clear = True
    except PaymentEmailValidationError:
        text = payment_email_validation_error_message()
        keyboard = build_payment_email_kbd()
    await message.answer(text, reply_markup=keyboard)
    if state_clear:
        await state.clear()
