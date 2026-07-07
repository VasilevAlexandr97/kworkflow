from uuid import UUID

from kworkflow.background_tasks.tasks import (
    generate_project_proposal_task,
    notify_project_proposal_generated_task,
    notify_subscription_activated,
)
from kworkflow.notifications.interfaces import (
    ProposalGeneratedNotificationQueue,
    SubscriptionActivatedNotificationQueue,
)
from kworkflow.projects.interfaces import (
    ProposalGenerationQueue,
)


class TaskiqProposalGenerationQueue(ProposalGenerationQueue):
    async def enqueue(self, user_id: UUID, project_id: UUID) -> None:
        await generate_project_proposal_task.kiq(
            user_id=user_id,
            project_id=project_id,
        )


class TaskiqProposalGeneratedNotificationQueue(
    ProposalGeneratedNotificationQueue,
):
    async def enqueue(self, user_id: UUID, project_id: UUID) -> None:
        await notify_project_proposal_generated_task.kiq(
            user_id=user_id,
            project_id=project_id,
        )


class TaskiqSubscriptionActivatedNotificationQueue(
    SubscriptionActivatedNotificationQueue,
):
    async def enqueue(self, user_id: UUID) -> None:
        await notify_subscription_activated.kiq(user_id=user_id)
