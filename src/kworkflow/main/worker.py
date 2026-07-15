import logging

from aiogram import Bot
from dishka.integrations.taskiq import setup_dishka

from kworkflow.infra.taskiq.broker import broker, scheduler
from kworkflow.main.config import Config, get_config
from kworkflow.main.di import (
    WorkerProvider,
    create_container,
)

config = get_config()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.telegram_bot.token)
container = create_container(
    providers=[WorkerProvider()],
    context={Config: config, Bot: bot},
)

setup_dishka(container, broker)

logger.debug(scheduler)
