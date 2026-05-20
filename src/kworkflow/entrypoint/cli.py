import asyncio

from dishka import make_async_container

from kworkflow.entrypoint.config import Config, get_config
from kworkflow.entrypoint.di import InfraProvider, ProjectProvider
from kworkflow.projects.services import ProjectCategoryService


async def main():
    config = get_config()
    container = make_async_container(
        InfraProvider(),
        ProjectProvider(),
        context={Config: config},
    )

    async with container() as c_req:
        service = await c_req.get(ProjectCategoryService)
        await service.import_categories()
    await container.close()


if __name__ == "__main__":
    asyncio.run(main())
