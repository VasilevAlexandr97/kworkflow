import logging

from aiogram import Bot
from dishka import make_async_container
from dishka.integrations.taskiq import setup_dishka

# TODO: Подумать как правильно импортировать scheduler
from kworkflow.infra.taskiq.broker import broker, scheduler

# from kworkflow.background_tasks.tasks import register_tasks
from kworkflow.main.config import Config, get_config
from kworkflow.main.di import (
    InfraProvider,
    NotificationProvider,
    PreferenceProvider,
    ProjectProvider,
    UserProvider,
    WorkerProvider,
)

logger = logging.getLogger(__name__)

config = get_config()


bot = Bot(token=config.telegram_bot.token)
container = make_async_container(
    InfraProvider(),
    UserProvider(),
    ProjectProvider(),
    PreferenceProvider(),
    NotificationProvider(),
    WorkerProvider(),
    context={Config: config, Bot: bot},
)

# register_tasks(broker)
setup_dishka(container, broker)
