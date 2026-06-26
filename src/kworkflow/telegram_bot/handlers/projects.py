from aiogram import F, Router, types
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from dishka.integrations.aiogram import FromDishka, inject

from kworkflow.preferences.exceptions import UserFreelancerProfileNotFoundError
from kworkflow.projects.exceptions import (
    ProjectProposalGenerationPermissionError,
)
from kworkflow.projects.services import ProjectProposalService
from kworkflow.telegram_bot.keyboards import GenerateProposalCB
from kworkflow.telegram_bot.messages import (
    FREELANCER_PROFILE_TEMPLATE_TEXT,
    GENERATE_PROPOSAL_PROFILE_REQUIRED_TEXT,
    project_proposal_generation_permission_error_message,
)
from kworkflow.telegram_bot.states import (
    FreelancerProfileState,
)

router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(
    F.message.chat.type == ChatType.PRIVATE,
)


@router.callback_query(GenerateProposalCB.filter())
@inject
async def generate_proposal(
    call: types.CallbackQuery,
    callback_data: GenerateProposalCB,
    service: FromDishka[ProjectProposalService],
    state: FSMContext,
):
    try:
        result = await service.generate_proposal(callback_data.project_id)
        text = result.generated_text
    except UserFreelancerProfileNotFoundError:
        text = (
            f"{GENERATE_PROPOSAL_PROFILE_REQUIRED_TEXT}"
            "\n\n"
            f"{FREELANCER_PROFILE_TEMPLATE_TEXT}"
        )
        await state.set_state(FreelancerProfileState.edit)
    except ProjectProposalGenerationPermissionError:
        text = project_proposal_generation_permission_error_message()
    await call.message.answer(text)
    await call.answer()
