import logging

from aiogram import Bot
from dishka import make_async_container
from dishka.integrations.taskiq import setup_dishka
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import (
    RedisAsyncResultBackend,
    RedisStreamBroker,
)

# from kworkflow.background_tasks.tasks import register_tasks
from kworkflow.main.config import Config, get_config
from kworkflow.main.di import (
    InfraProvider,
    NotificationProvider,
    PreferenceProvider,
    ProjectProvider,
    WorkerProvider,
)

logger = logging.getLogger(__name__)

config = get_config()

result_backend = RedisAsyncResultBackend(
    redis_url=config.redis.connection_url,
    result_ex_time=3600,
)
broker = RedisStreamBroker(
    url=config.redis.connection_url,
).with_result_backend(result_backend)

scheduler = TaskiqScheduler(broker, sources=[LabelScheduleSource(broker)])

bot = Bot(token=config.telegram_bot.token)
container = make_async_container(
    InfraProvider(),
    ProjectProvider(),
    PreferenceProvider(),
    NotificationProvider(),
    WorkerProvider(),
    context={Config: config, Bot: bot},
)

# register_tasks(broker)
setup_dishka(container, broker)
