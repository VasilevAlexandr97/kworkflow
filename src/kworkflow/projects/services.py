import html
import logging
import re

from datetime import UTC, datetime
from uuid import UUID, uuid7

from kworkflow.auth.id_provider import IdProvider
from kworkflow.infra.database.transaction_manager import TransactionManager
from kworkflow.infra.kwork.client import KworkClient
from kworkflow.preferences.exceptions import UserFreelancerProfileNotFoundError
from kworkflow.preferences.gateways import UserFreelancerProfileGateway
from kworkflow.projects.exceptions import (
    ProjectNotFoundError,
    ProjectProposalGenerationError,
)
from kworkflow.projects.gateway import (
    ProjectCategoryGateway,
    ProjectGateway,
    ProjectProposalGateway,
)
from kworkflow.projects.generators import ProjectProposalGenerator
from kworkflow.projects.models import Project, ProjectCategory, ProjectProposal

logger = logging.getLogger(__name__)


class ProjectCategoryService:
    def __init__(
        self,
        gateway: ProjectCategoryGateway,
        kwork_client: KworkClient,
        transaction_manager: TransactionManager,
    ):
        self.gateway = gateway
        self.kwork_client = kwork_client
        self.transaction_manager = transaction_manager

    async def import_categories(self):
        categories_data = []
        categories = await self.kwork_client.get_categories()
        for category in categories:
            parent_id = uuid7()
            categories_data.extend(
                (
                    {
                        "id": parent_id,
                        "external_id": category.id,
                        "title": category.name,
                        "parent_id": None,
                    },
                    *(
                        {
                            "id": uuid7(),
                            "external_id": sub.id,
                            "title": sub.name,
                            "parent_id": parent_id,
                        }
                        for sub in category.subcategories or []
                    ),
                ),
            )
        await self.gateway.upsert(categories_data)
        await self.transaction_manager.commit()

    async def get_root_categories(self) -> list[ProjectCategory]:
        return await self.gateway.get_root_categories()

    async def get_subcategories(
        self,
        parent_id: UUID,
    ) -> list[ProjectCategory]:
        return await self.gateway.get_child_categories(parent_id)


class ProjectSyncService:
    def __init__(
        self,
        kwork_client: KworkClient,
        category_gateway: ProjectCategoryGateway,
        project_gateway: ProjectGateway,
        transaction_manager: TransactionManager,
    ):
        self.kwork_client = kwork_client
        self.category_gateway = category_gateway
        self.project_gateway = project_gateway
        self.transaction_manager = transaction_manager

    def _clean_project_description(self, text: str):
        # 1. Декодируем HTML entities
        text = html.unescape(text)

        # 2. <br> -> перенос строки
        text = re.sub(r"<br\s*/?>", "\n", text)

        # 3. Удаляем остальные HTML-теги
        text = re.sub(r"<[^>]+>", "", text)

        # 4. Нормализуем переносы строк
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 5. Убираем лишние пробелы
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    async def get_and_save_new_projects(self):
        projects = await self.kwork_client.get_projects(categories_ids=["all"])
        project_ids = [project.id for project in projects if project.id]
        new_project_ids = await self.project_gateway.get_missing_external_ids(
            project_ids,
        )
        category_ids = [
            project.category_id for project in projects if project.category_id
        ]
        categories = (
            await self.category_gateway.get_categories_by_external_ids(
                category_ids,
            )
        )
        categories_map = {
            category.external_id: category.id for category in categories
        }
        new_projects: list[Project] = []
        if new_project_ids:
            new_projects.extend(
                Project(
                    id=uuid7(),
                    external_id=project.id,
                    category_id=categories_map[project.category_id],
                    price=project.price,
                    possible_price_limit=project.possible_price_limit,
                    title=project.title,
                    description=self._clean_project_description(
                        project.description,
                    ),
                    offers=project.offers,
                )
                for project in projects
                if project.id in new_project_ids
            )
        if new_projects:
            await self.project_gateway.bulk_insert(new_projects)
            await self.transaction_manager.commit()
        return [project.id for project in new_projects]


class ProjectProposalService:
    def __init__(
        self,
        id_provider: IdProvider,
        project_gateway: ProjectGateway,
        project_proposal_gateway: ProjectProposalGateway,
        freelancer_profile_gateway: UserFreelancerProfileGateway,
        proposal_generator: ProjectProposalGenerator,
        transaction_manager: TransactionManager,
    ):
        self.id_provider = id_provider
        self.project_gateway = project_gateway
        self.project_proposal_gateway = project_proposal_gateway
        self.freelancer_profile_gateway = freelancer_profile_gateway
        self.proposal_generator = proposal_generator
        self.transaction_manager = transaction_manager

    def _build_project_info(self, project: Project) -> str:
        return f"Название: {project.title}\n\nЗадание: {project.description}"

    async def generate_proposal(self, project_id: UUID) -> ProjectProposal:
        user_id = await self.id_provider.get_current_user_id()
        freelancer_profile = await self.freelancer_profile_gateway.get(user_id)
        if freelancer_profile is None:
            raise UserFreelancerProfileNotFoundError

        project = await self.project_gateway.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError

        project_proposal = await self.project_proposal_gateway.get(
            project_id=project_id,
            user_id=user_id,
        )
        if project_proposal:
            return project_proposal
        try:
            project_info = self._build_project_info(project)
            result = await self.proposal_generator.generate(
                freelancer_info=freelancer_profile.about,
                project_info=project_info,
            )
            logger.debug(f"RESULT GENERATION: {result}")
        except ProjectProposalGenerationError:
            logger.info(f"Project info: {project_info}")
            logger.info(f"Freelancer info: {freelancer_profile.about}")
            logger.info("Project proposal generation error")
            raise
        project_proposal = ProjectProposal(
            id=uuid7(),
            project_id=project_id,
            user_id=user_id,
            generated_text=result.text,
            prompt=result.prompt,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            cost=result.cost,
            created_at=datetime.now(UTC),
        )
        await self.project_proposal_gateway.add(project_proposal)
        await self.transaction_manager.commit()
        return project_proposal
