import asyncio
import json

import aiohttp
import requests
from django.conf import settings

from apps.githubs.models import GithubUser, UserOrganization, Organization
from core.github_dto import OrganizationDto, RepositoryDto
from utils.exceptions import manage_api_call_fail
from core.repository_service import RepositoryService


class OrganizationService:

    def __init__(self, github_user: GithubUser):
        self.github_user = github_user
        self.new_repositories = []  # 업데이트 해야할 레포지토리
        self.repositories = []  # 실제 유저의 레포지토리

    @staticmethod
    def create_dto(organization_data: dict) -> OrganizationDto:
        return OrganizationDto(
            name=organization_data.get('login'),
            description=organization_data.get('description'),
            logo=organization_data.get('avatar_url'),
            repos_url=organization_data.get('repos_url')
        )

    def update_organization(self, organization_url: str):
        """
        organization(소속) 업데이트 함
        """

        res = requests.get(organization_url, headers=settings.GITHUB_API_HEADER)
        if res.status_code != 200:
            manage_api_call_fail(self.github_user, res.status_code)

        update_user_organization_list = []
        user_organizations = list(UserOrganization.objects.filter(
            github_user_id=self.github_user.id).values_list('organization__name', flat=True)
        )

        try:
            organizations = []
            for organization_data in json.loads(res.content):
                org_dto = self.create_dto(organization_data)
                organizations.append(org_dto)

        except json.JSONDecodeError:
            return

        for organization_dto in organizations:
            try:
                update_fields = []
                organization = Organization.objects.get(name=organization_dto.name)

                for idx, org in enumerate(user_organizations):
                    if organization.name == org:
                        user_organizations.pop(idx)
                        break

                if organization.description != organization_dto.description:
                    organization.description = organization_dto.description
                    update_fields.append('description')

                if organization.logo != organization_dto.logo:
                    organization.logo = organization_dto.logo
                    update_fields.append('logo')

                if update_fields:
                    organization.save(update_fields=update_fields)

                update_user_organization_list.append(organization.id)

            except Organization.DoesNotExist:
                new_organization = Organization.objects.create(
                    name=organization_dto.name,
                    logo=organization_dto.logo,
                    description=organization_dto.description or '',
                )
                update_user_organization_list.append(new_organization.id)

            # organization 에 있는 repository 중 User 가 Contributor 인 repository 를 등록한다.
            res = requests.get(organization_dto.repos_url, headers=settings.GITHUB_API_HEADER)
            if res.status_code != 200:
                manage_api_call_fail(self.github_user, res.status_code)

            try:
                repositories = []
                repository_service = RepositoryService(github_user=self.github_user)

                for repository_data in json.loads(res.content):
                    repository_dto = repository_service.create_dto(repository_data)
                    repositories.append(repository_dto)

            except json.JSONDecodeError:
                continue

            self.new_repositories += repositories

        new_user_organization_list = []
        for organization_id in update_user_organization_list:
            if not UserOrganization.objects.filter(
                github_user_id=self.github_user.id,
                organization_id=organization_id
            ).exists():
                new_user_organization_list.append(
                    UserOrganization(
                        github_user_id=self.github_user.id,
                        organization_id=organization_id
                    )
                )

        if new_user_organization_list:
            UserOrganization.objects.bulk_create(new_user_organization_list)

        if user_organizations:
            UserOrganization.objects.filter(
                github_user_id=self.github_user.id,
                organization__name__in=user_organizations
            ).delete()

    def get_organization_repository(self):
        """
        organization 에 저장되어있는 repository 정보를 가져온다
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.save_organization_repository_futures(self.new_repositories))

    async def append_organization_repository(self, repository: RepositoryDto):  # 코루틴 정의
        async with aiohttp.ClientSession() as session:
            async with session.get(repository.contributors_url, headers=settings.GITHUB_API_HEADER) as res:
                response_text = await res.text()

                if res.status != 200:
                    return

                # 451은 레포지토리 접근 오류('Repository access blocked') - 저작권에 따라 block 될 수 있음
                for contributor in json.loads(response_text):
                    if self.github_user.username.lower() == contributor.get('login').lower():
                        self.repositories.append(repository)
                        break

    async def save_organization_repository_futures(self, repositories: list):
        futures = [
            asyncio.ensure_future(self.append_organization_repository(repository)) for repository in repositories
        ]

        await asyncio.gather(*futures)
