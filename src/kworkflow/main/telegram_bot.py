import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from dishka import make_async_container
from dishka.integrations.aiogram import AiogramProvider, setup_dishka

from kworkflow.main.config import Config, config
from kworkflow.main.di import (
    InfraProvider,
    PreferenceProvider,
    ProjectProvider,
    TelegramBotProvider,
    UserProvider,
)
from kworkflow.telegram_bot.handlers.default import router as default_router
from kworkflow.telegram_bot.handlers.preferences import (
    router as preferences_router,
)

bot = Bot(
    token=config.telegram_bot.token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
container = make_async_container(
    InfraProvider(),
    UserProvider(),
    ProjectProvider(),
    PreferenceProvider(),
    AiogramProvider(),
    TelegramBotProvider(),
    context={Config: config, Bot: bot},
)


def setup_handlers(dp: Dispatcher):
    dp.include_router(default_router)
    dp.include_router(preferences_router)


def get_dispatcher() -> Dispatcher:
    logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO)
    storage = RedisStorage.from_url(config.redis.connection_url)
    dp = Dispatcher(storage=storage)
    setup_handlers(dp)
    setup_dishka(container, dp)
    return dp


def run_polling():
    dp = get_dispatcher()
    dp.run_polling(bot)
