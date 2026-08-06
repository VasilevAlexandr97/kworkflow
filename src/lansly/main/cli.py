import argparse
import asyncio
import logging

from aiogram import Bot

from lansly.main.config import Config, get_config
from lansly.main.di import (
    WorkerProvider,
    create_container,
)
from lansly.projects.services import ProjectCategoryService
from lansly.users.service import CreateAdminUserService

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lansly")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("import-categories")
    admin = sub.add_parser("create-admin")
    admin.add_argument("--username", required=True)
    admin.add_argument("--password", required=True)
    return parser


async def main():
    logging.basicConfig(level=logging.INFO)
    config = get_config()
    bot = Bot(token=config.telegram_bot.token)
    container = create_container(
        providers=[WorkerProvider()],
        context={Config: config, Bot: bot},
    )

    args = build_parser().parse_args()
    async with container() as c_req:
        if args.command == "import-categories":
            service = await c_req.get(ProjectCategoryService)
            await service.import_categories()
        elif args.command == "create-admin":
            service = await c_req.get(CreateAdminUserService)
            await service.create(args.username, args.password)
            logger.info("Admin user created")
    await container.close()


if __name__ == "__main__":
    asyncio.run(main())
