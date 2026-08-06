from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from lansly.subscriptions.models import PlanSlug


@dataclass(frozen=True)
class SubscriptionInfoDTO:
    plan_name: str
    plan_slug: PlanSlug
    is_cancelled: bool
    started_at: datetime
    expires_at: datetime
    days_left: int


@dataclass(frozen=True)
class PlanForUserDTO:
    slug: PlanSlug
    price: Decimal
    monthly_price: Decimal
    duration_days: int
