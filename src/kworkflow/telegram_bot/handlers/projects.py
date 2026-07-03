from aiogram import F, Router, types
from aiogram.enums import ChatType
from dishka.integrations.aiogram import FromDishka, inject

from kworkflow.preferences.exceptions import UserFreelancerProfileNotFoundError
from kworkflow.projects.dto import ProjectProposalGenerationRequestStatus
from kworkflow.projects.exceptions import (
    ProjectProposalGenerationPermissionError,
)
from kworkflow.projects.services import (
    ProjectProposalRequestService,
)
from kworkflow.telegram_bot.keyboards import (
    GenerateProposalCB,
    build_profile_menu_kbd,
)
from kworkflow.telegram_bot.messages import (
    profile_not_set_message,
    project_proposal_generation_permission_error_message,
)

router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(
    F.message.chat.type == ChatType.PRIVATE,
)


@router.callback_query(GenerateProposalCB.filter())
@inject
async def generate_proposal_request(
    call: types.CallbackQuery,
    callback_data: GenerateProposalCB,
    service: FromDishka[ProjectProposalRequestService],
):
    try:
        result = await service.request_generation(callback_data.project_id)
        if result.status == ProjectProposalGenerationRequestStatus.CREATED:
            await call.answer("Генерирую", show_alert=True)

        elif (
            result.status
            == ProjectProposalGenerationRequestStatus.ALREADY_PENDING
        ):
            await call.answer("Уже генерирую", show_alert=True)

        elif (
            result.status
            == ProjectProposalGenerationRequestStatus.ALREADY_GENERATED
            and result.generated_text
        ):
            await call.message.answer(result.generated_text)
            await call.answer()
    except UserFreelancerProfileNotFoundError:
        text = profile_not_set_message()
        keyboard = build_profile_menu_kbd()
        await call.message.answer(text, reply_markup=keyboard)
        await call.answer()
    except ProjectProposalGenerationPermissionError:
        text = project_proposal_generation_permission_error_message()
        await call.message.answer(text)
        await call.answer()
