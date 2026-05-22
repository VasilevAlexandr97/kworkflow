import logging

from uuid import UUID

from dishka.integrations.taskiq import FromDishka, inject

# from taskiq_redis import RedisStreamBroker
from kworkflow.main.worker import broker
from kworkflow.notifications.services import ProjectNotificationService
from kworkflow.projects.services import ProjectSyncService

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


# def register_tasks(broker: RedisStreamBroker):
#     broker.register_task(
#         monitoring_new_projects,
#         ,
#     )
