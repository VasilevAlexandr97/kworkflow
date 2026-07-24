import logging

from aiogram import Bot
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from kworkflow.main.config import Config, get_config
from kworkflow.main.di import WebProvider, create_container
from kworkflow.web.middlewares.security import SecurityHeadersMiddleware
from kworkflow.web.routers.index import router as index_router
from kworkflow.web.routers.robots import router as robots_router
from kworkflow.web.routers.sitemap import router as sitemap_router


def setup_middlewares(app: FastAPI):
    app.add_middleware(SecurityHeadersMiddleware)


def setup_routers(app: FastAPI):
    app.include_router(index_router)
    app.include_router(robots_router)
    app.include_router(sitemap_router)


def create_app():
    config = get_config()
    logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO)
    bot = Bot(token=config.telegram_bot.token)
    container = create_container(
        providers=[WebProvider()],
        context={Config: config, Bot: bot},
    )
    if config.debug:
        app = FastAPI(debug=config.debug)
    else:
        app = FastAPI(
            debug=config.debug,
            docs_url=None,
            redoc_url=None,
            openapi_url=None,
        )
    app.mount(
        "/static",
        StaticFiles(directory=config.web.static_dir),
        name="static",
    )
    setup_middlewares(app)
    setup_routers(app)
    setup_dishka(container, app)
    return app
