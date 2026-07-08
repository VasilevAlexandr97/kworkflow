from dataclasses import dataclass
from datetime import datetime

from kworkflow.subscriptions.models import PlanSlug


@dataclass(frozen=True)
class SubscriptionInfo:
    plan_name: str
    plan_slug: PlanSlug
    is_cancelled: bool
    started_at: datetime
    expires_at: datetime
    days_left: int
