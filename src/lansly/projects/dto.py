from dataclasses import dataclass
from enum import StrEnum


class ProjectProposalGenerationRequestStatus(StrEnum):
    CREATED = "created"
    ALREADY_PENDING = "already_pending"
    ALREADY_GENERATED = "already_generated"


@dataclass(frozen=True)
class ProjectProposalGenerationRequestResult:
    status: ProjectProposalGenerationRequestStatus
    generated_text: str | None = None
