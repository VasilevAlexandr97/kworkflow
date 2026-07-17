import logging

from datetime import UTC, datetime
from uuid import UUID

from kworkflow.auth.id_provider import IdProvider
from kworkflow.common.interfaces.subscription_checker import (
    SubscriptionChecker,
)
from kworkflow.infra.database.transaction_manager import TransactionManager
from kworkflow.preferences.consts import (
    MAX_FREE_CATEGORIES,
    MAX_FREE_STOP_WORDS,
    MAX_LENGTH_STOP_WORD,
    MAX_PRO_CATEGORIES,
    MAX_PRO_STOP_WORDS,
)
from kworkflow.preferences.dto import (
    CategoryWithFollowedStatusDTO,
    CountStopWordsDTO,
    StopWordsDTO,
    SubcategoriesWithFollowStatusDTO,
)
from kworkflow.preferences.exceptions import (
    UserCategoryFollowAlreadyExistsError,
    UserCategoryFollowLimitExceededError,
)
from kworkflow.preferences.gateways import (
    UserCategoryFollowGateway,
    UserFreelancerProfileGateway,
    UserStopWordsGateway,
)
from kworkflow.preferences.models import (
    UserCategoryFollow,
    UserFreelancerProfile,
    UserStopWord,
)
from kworkflow.projects.exceptions import ProjectCategoryNotFoundError
from kworkflow.projects.models import ProjectCategory

logger = logging.getLogger(__name__)


class UserCategoryFollowService:
    def __init__(
        self,
        follow_gateway: UserCategoryFollowGateway,
        subscription_checker: SubscriptionChecker,
        id_provider: IdProvider,
        transaction_manager: TransactionManager,
    ):
        self.follow_gateway = follow_gateway
        self.subscription_checker = subscription_checker
        self.id_provider = id_provider
        self.transaction_manager = transaction_manager

    async def _get_subcategories_with_follow_status(
        self,
        user_id: UUID,
        parent_id: UUID,
    ) -> list[CategoryWithFollowedStatusDTO]:
        rows = await self.follow_gateway.get_subcategories_with_follow_status(
            user_id=user_id,
            parent_id=parent_id,
        )
        return [
            CategoryWithFollowedStatusDTO(category=row[0], is_followed=row[1])
            for row in rows
        ]

    async def get_subcategories_with_follow_status(
        self,
        parent_id: UUID,
    ) -> list[CategoryWithFollowedStatusDTO]:
        user_id = await self.id_provider.get_current_user_id()
        return await self._get_subcategories_with_follow_status(
            user_id=user_id,
            parent_id=parent_id,
        )

    async def _get_followed_categories(
        self,
        user_id: UUID,
    ) -> list[ProjectCategory]:
        follows = await self.follow_gateway.get_follows_with_category(user_id)
        return [follow.category for follow in follows]

    async def get_followed_categories(self) -> list[ProjectCategory]:
        user_id = await self.id_provider.get_current_user_id()
        return await self._get_followed_categories(user_id)

    async def unfollow_all_categories(self) -> list[ProjectCategory]:
        user_id = await self.id_provider.get_current_user_id()
        await self.follow_gateway.deactivate_all(user_id)
        await self.transaction_manager.commit()
        return await self._get_followed_categories(user_id)

    async def _get_user_limit_and_available(self, user_id: UUID) -> int:
        is_pro_user = await self.subscription_checker.is_pro_user(user_id)
        return MAX_FREE_CATEGORIES if not is_pro_user else MAX_PRO_CATEGORIES

    async def toggle_category_follow(
        self,
        category_id: UUID,
    ) -> SubcategoriesWithFollowStatusDTO:
        user_id = await self.id_provider.get_current_user_id()
        category = await self.follow_gateway.get_category(category_id)
        if not category:
            raise ProjectCategoryNotFoundError
        follow = await self.follow_gateway.get(
            user_id=user_id,
            category_id=category_id,
        )
        now = datetime.now(UTC)
        limit = await self._get_user_limit_and_available(user_id)

        if follow:
            if follow.is_active:
                follow.is_active = False
            else:
                count = (
                    await self.follow_gateway.get_count_followed_categories(
                        user_id,
                    )
                )
                if count + 1 > limit:
                    raise UserCategoryFollowLimitExceededError(limit=limit)
                follow.is_active = True
            follow.updated_at = now
            await self.transaction_manager.commit()
        else:
            count = await self.follow_gateway.get_count_followed_categories(
                user_id,
            )
            if count + 1 > limit:
                raise UserCategoryFollowLimitExceededError(limit=limit)
            new_follow = UserCategoryFollow(
                user_id=user_id,
                category_id=category_id,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            try:
                await self.follow_gateway.add(new_follow)
                await self.transaction_manager.commit()
            except UserCategoryFollowAlreadyExistsError:
                logger.info(
                    "UserCategoryFollow Already Exists "
                    f"user_id={user_id}, category_id={category_id}",
                )
        # parent_id переработать метод и забирать из UserCategoryFollow
        subcategories = await self._get_subcategories_with_follow_status(
            user_id=user_id,
            parent_id=category.parent_id,
        )
        return SubcategoriesWithFollowStatusDTO(
            categories=subcategories,
            limit=limit,
        )


class UserFreelancerProfileService:
    def __init__(
        self,
        profile_gateway: UserFreelancerProfileGateway,
        id_provider: IdProvider,
        transaction_manager: TransactionManager,
    ):
        self.profile_gateway = profile_gateway
        self.id_provider = id_provider
        self.transaction_manager = transaction_manager

    async def get_profile(self) -> UserFreelancerProfile | None:
        user_id = await self.id_provider.get_current_user_id()
        return await self.profile_gateway.get(user_id)

    async def edit_or_create_profile(
        self,
        about_text: str,
    ) -> UserFreelancerProfile:
        user_id = await self.id_provider.get_current_user_id()
        profile = await self.profile_gateway.get(user_id)
        if profile is not None:
            profile.about = about_text
        else:
            profile = UserFreelancerProfile(
                user_id=user_id,
                about=about_text,
            )
            await self.profile_gateway.add(profile)
        await self.transaction_manager.commit()
        return profile


class UserStopWordsService:
    def __init__(
        self,
        stop_words_gateway: UserStopWordsGateway,
        subscription_checker: SubscriptionChecker,
        id_provider: IdProvider,
        transaction_manager: TransactionManager,
    ):
        self.stop_words_gateway = stop_words_gateway
        self.subscription_checker = subscription_checker
        self.id_provider = id_provider
        self.transaction_manager = transaction_manager

    async def _get_user_limit_and_available(
        self,
        user_id: UUID,
        current_count: int,
    ) -> tuple[int, int]:
        is_pro_user = await self.subscription_checker.is_pro_user(user_id)
        limit = MAX_FREE_STOP_WORDS if not is_pro_user else MAX_PRO_STOP_WORDS
        available = max(limit - current_count, 0)
        return limit, available

    async def add_stop_words(self, words: list[str]) -> StopWordsDTO:
        logger.debug(f"ADD STOP WORDS LIST: {words}")
        user_id = await self.id_provider.get_current_user_id()
        current_stop_words = (
            await self.stop_words_gateway.get_stop_words_by_user_id(
                user_id,
            )
        )
        limit, available = await self._get_user_limit_and_available(
            user_id=user_id,
            current_count=len(current_stop_words),
        )
        if available == 0:
            return StopWordsDTO(
                words=current_stop_words,
                available=available,
                limit=limit,
            )
        now = datetime.now(UTC)
        new_stop_words = [
            UserStopWord(
                user_id=user_id,
                word=word.lower().strip(),
                created_at=now,
            )
            for word in words
            if word.strip()
            and len(word.strip()) <= MAX_LENGTH_STOP_WORD
            and word.lower().strip() not in current_stop_words
        ]
        new_stop_words = new_stop_words[:available]
        if new_stop_words:
            await self.stop_words_gateway.add_batch(new_stop_words)
            await self.transaction_manager.commit()
        full_stop_words = (
            await self.stop_words_gateway.get_stop_words_by_user_id(
                user_id,
            )
        )
        limit, available = await self._get_user_limit_and_available(
            user_id=user_id,
            current_count=len(full_stop_words),
        )
        return StopWordsDTO(
            words=full_stop_words,
            available=available,
            limit=limit,
        )

    async def delete_stop_words(self, words: list[str]) -> StopWordsDTO:
        user_id = await self.id_provider.get_current_user_id()
        stop_words = [word.lower().strip() for word in words]
        if stop_words:
            await self.stop_words_gateway.delete_batch(user_id, stop_words)
            await self.transaction_manager.commit()
        new_stop_words = (
            await self.stop_words_gateway.get_stop_words_by_user_id(user_id)
        )
        limit, available = await self._get_user_limit_and_available(
            user_id=user_id,
            current_count=len(new_stop_words),
        )
        return StopWordsDTO(
            words=new_stop_words,
            available=available,
            limit=limit,
        )

    async def get_stop_words(self) -> StopWordsDTO:
        user_id = await self.id_provider.get_current_user_id()
        stop_words = await self.stop_words_gateway.get_stop_words_by_user_id(
            user_id,
        )
        limit, available = await self._get_user_limit_and_available(
            user_id,
            current_count=len(stop_words),
        )
        return StopWordsDTO(
            words=stop_words,
            available=available,
            limit=limit,
        )

    async def count_stop_words(self) -> CountStopWordsDTO:
        user_id = await self.id_provider.get_current_user_id()
        count = await self.stop_words_gateway.count_stop_words_by_user_id(
            user_id,
        )
        limit, available = await self._get_user_limit_and_available(
            user_id=user_id,
            current_count=count,
        )
        return CountStopWordsDTO(count=count, available=available, limit=limit)
