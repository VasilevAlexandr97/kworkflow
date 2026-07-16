import logging

from aiogram import Bot
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from kworkflow.main.config import Config, get_config
from kworkflow.main.di import WebProvider, create_container
from kworkflow.web.routers.index import router as index_router


def setup_routers(app: FastAPI):
    app.include_router(index_router)


def create_app():
    config = get_config()
    logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO)
    bot = Bot(token=config.telegram_bot.token)
    container = create_container(
        providers=[WebProvider()],
        context={Config: config, Bot: bot},
    )
    app = FastAPI(debug=config.debug)
    setup_routers(app)
    setup_dishka(container, app)
    return app
