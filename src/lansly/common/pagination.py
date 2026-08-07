from dataclasses import dataclass


@dataclass
class PaginationParams:
    page: int = 1
    per_page: int = 10

    def __post_init__(self):
        max_per_page = 100
        if self.page <= 0:
            self.page = 1
        if self.per_page <= 0 or self.per_page > max_per_page:
            self.per_page = 10


@dataclass(frozen=True)
class PaginationResponse[T]:
    items: list[T]
    total: int
    page: int
    per_page: int
