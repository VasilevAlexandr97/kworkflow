from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class AuthSession:
    id: str
    user_id: UUID
    expires_at: datetime
