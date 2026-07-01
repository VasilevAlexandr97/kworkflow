import logging

from uuid import UUID

from dishka.integrations.taskiq import FromDishka, inject

from kworkflow.infra.taskiq.broker import broker
from kworkflow.notifications.services import (
    ProjectNotificationService,
    ProjectProposalNotificationService,
)
from kworkflow.projects.services import (
    ProjectSyncService,
    ProjectProposalGenerationService,
)

logger = logging.getLogger(__name__)


@broker.task(schedule=[{"cron": "* * * * *"}])
@inject
async def monitoring_new_projects(
    service: FromDishka[ProjectSyncService],
):
    new_projects = await service.get_and_save_new_projects()
    logger.info(f"NEW PROJECTS: {new_projects}")
    if new_projects:
        await notify_new_projects.kiq(new_projects)


@broker.task()
@inject
async def notify_new_projects(
    new_projects: list[UUID],
    service: FromDishka[ProjectNotificationService],
):
    await service.notify_new_projects(new_projects)


@broker.task()
@inject
async def generate_project_proposal_task(
    user_id: UUID,
    project_id: UUID,
    service: FromDishka[ProjectProposalGenerationService],
):
    logger.info(
        f"DO GENERATE PROJECT PROPOSAL TASK: user_id={user_id}, project_id={project_id}"
    )
    await service.generate_proposal_for_user(
        user_id=user_id,
        project_id=project_id,
    )


@broker.task()
@inject
async def notify_project_proposal_generated_task(
    user_id: UUID,
    project_id: UUID,
    service: FromDishka[ProjectProposalNotificationService],
):
    await service.notify_generated(user_id=user_id, project_id=project_id)
