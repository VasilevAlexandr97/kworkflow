from lansly.projects.models import ProjectCategory


# TODO: подумать добавить или нет интерфейс для основного сервиса
class FakeFollowService:
    def __init__(self, categories: list[ProjectCategory] | None = None):
        self.categories = categories or []
        self.get_followed_categories_calls = 0

    async def get_followed_categories(self) -> list[ProjectCategory]:
        self.get_followed_categories_calls += 1
        return self.categories
