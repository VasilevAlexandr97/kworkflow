import asyncio
import sys

from aiogram import Bot
from dishka import make_async_container

from kworkflow.main.config import Config, get_config
from kworkflow.main.di import (
    InfraProvider,
    NotificationProvider,
    PreferenceProvider,
    ProjectProvider,
    WorkerProvider,
)
from kworkflow.notifications.services import ProjectNotificationService
from kworkflow.projects.services import ProjectCategoryService


async def main():
    config = get_config()
    bot = Bot(token=config.telegram_bot.token)
    container = make_async_container(
        InfraProvider(),
        ProjectProvider(),
        PreferenceProvider(),
        NotificationProvider(),
        WorkerProvider(),
        context={Config: config, Bot: bot},
    )

    command = sys.argv[1]

    async with container() as c_req:
        if command == "import-categories":
            service = await c_req.get(ProjectCategoryService)
            await service.import_categories()
        else:
            service = await c_req.get(ProjectNotificationService)
            await service.notify_new_projects()
    await container.close()


if __name__ == "__main__":
    asyncio.run(main())
