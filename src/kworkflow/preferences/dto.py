from dataclasses import dataclass

from kworkflow.projects.models import ProjectCategory


@dataclass
class CategoryFollowStatusDTO:
    category: ProjectCategory
    is_followed: bool


@dataclass
class FollowCategoryDTO:
    category_id: UUID
    title: str