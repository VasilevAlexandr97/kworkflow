import logging

from contextlib import asynccontextmanager

from aiogram import Bot
from dishka import AsyncContainer
from dishka.integrations.fastapi import FastapiProvider, setup_dishka
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.contrib.sqla import Admin

from kworkflow.admin_panel.auth import AdminPanelAuthProvider
from kworkflow.admin_panel.views.projects import (
    ProjectProposalView,
    ProjectView,
)
from kworkflow.admin_panel.views.users import UserView
from kworkflow.main.config import Config, get_config
from kworkflow.main.di import (
    AdminPanelProvider,
    AuthProvider,
    create_container,
)
from kworkflow.projects.models import Project, ProjectProposal
from kworkflow.users.models import User

logger = logging.getLogger(__name__)


def setup_views(admin: Admin):
    admin.add_view(UserView(User))
    admin.add_view(ProjectView(Project))
    admin.add_view(ProjectProposalView(ProjectProposal))


def setup_admin(engine: AsyncEngine, app: FastAPI, config: Config):
    admin = Admin(
        engine=engine,
        debug=config.debug,
        auth_provider=AdminPanelAuthProvider(),
        middlewares=[
            Middleware(
                SessionMiddleware,
                session_cookie="__adm_s",
                max_age=config.admin_panel.session_ttl,
                secret_key=config.admin_panel.session_secret_key,
                same_site="strict",
            ),
        ],
    )
    setup_views(admin)
    admin.mount_to(app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    container: AsyncContainer = app.state.dishka_container
    engine = await container.get(AsyncEngine)
    config = await container.get(Config)
    setup_admin(engine=engine, app=app, config=config)
    logger.info("Admin panel started")
    yield
    logger.info("Stopping admin panel")
    await container.close()


def create_app():
    config = get_config()
    logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO)
    bot = Bot(token=config.telegram_bot.token)
    container = create_container(
        providers=[AdminPanelProvider(), AuthProvider(), FastapiProvider()],
        context={Config: config, Bot: bot},
    )
    app = FastAPI(debug=config.debug, lifespan=lifespan)
    setup_dishka(container, app)
    return app
