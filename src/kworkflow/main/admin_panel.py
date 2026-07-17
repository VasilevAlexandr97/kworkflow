import logging

from contextlib import asynccontextmanager

from aiogram import Bot
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette_admin.contrib.sqla import Admin

from kworkflow.admin_panel.views.projects import (
    ProjectProposalView,
    ProjectView,
)
from kworkflow.admin_panel.views.users import UserView
from kworkflow.main.config import Config, get_config
from kworkflow.main.di import AdminPanelProvider, create_container
from kworkflow.projects.models import Project, ProjectProposal
from kworkflow.users.models import User

logger = logging.getLogger(__name__)


def setup_views(admin: Admin):
    admin.add_view(UserView(User))
    admin.add_view(ProjectView(Project))
    admin.add_view(ProjectProposalView(ProjectProposal))


def setup_admin(engine: AsyncEngine, app: FastAPI):
    admin = Admin(engine=engine)
    setup_views(admin)
    admin.mount_to(app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    container: AsyncContainer = app.state.dishka_container
    engine = await container.get(AsyncEngine)
    setup_admin(engine, app)
    logger.info("Admin panel started")
    yield
    logger.info("Stopping admin panel")
    await container.close()


def create_app():
    config = get_config()
    logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO)
    bot = Bot(token=config.telegram_bot.token)
    container = create_container(
        providers=[AdminPanelProvider()],
        context={Config: config, Bot: bot},
    )
    app = FastAPI(debug=config.debug, lifespan=lifespan)
    setup_dishka(container, app)
    return app
