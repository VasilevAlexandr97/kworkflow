from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AdminUserDTO:
    user_id: UUID
    username: str
