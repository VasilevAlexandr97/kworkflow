from kwork import Kwork
from kwork.schema.category import ParentCategory


class KworkClient:
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.client = Kwork(login=self.login, password=self.password)

    async def get_categories(self) -> list[ParentCategory]:
        async with self.client as api:
            categories = await api.get_categories()
            return categories
