from dataclasses import dataclass
from uuid import UUID

from kworkflow.projects.models import ProjectCategory


@dataclass
class CategoryWithFollowedStatusDTO:
    category: ProjectCategory
    is_followed: bool


@dataclass
class FollowCategoryDTO:
    category_id: UUID
    title: str
