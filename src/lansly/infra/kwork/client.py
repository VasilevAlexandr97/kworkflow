from kwork import Kwork
from kwork.schema.category import ParentCategory
from kwork.schema.project import WantWorker


class KworkClient:
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.client = Kwork(
            login=self.login,
            password=self.password,
            retry_max_attempts=3,
            timeout=30,
        )

    async def get_categories(self) -> list[ParentCategory]:
        async with self.client as api:
            categories = await api.get_categories()
            return categories

    async def get_projects(
        self,
        categories_ids: list[int | str],
        page: int = 1,
    ) -> list[WantWorker]:
        async with self.client as api:
            projects = await api.get_projects(
                categories_ids=categories_ids,
                page=page,
            )
            return projects
