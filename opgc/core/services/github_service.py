from dataclasses import asdict
from typing import Optional

from django.db.models import Count
from sentry_sdk import capture_exception

from adapter.githubs import GithubAdapter
from apps.githubs.models import GithubUser
from core.github_dto import UserInformationDto
from utils.exceptions import RateLimit, insert_queue
from core.services.organization_service import OrganizationService
from core.services.repository_service import RepositoryService
from utils.github import get_continuous_commit_day
from utils.slack import SlackService


class GithubInformationService:
    github_user = None
    github_adapter = GithubAdapter
    github_api_per_page = 50

    user_update_fields = [
        'avatar_url', 'company', 'bio', 'blog', 'public_repos',
        'followers', 'following', 'name', 'email', 'location'
    ]

    def __init__(self, username: Optional[str] = None, is_insert_queue: bool = True):
        self.username = username
        self.new_repository_list = []  # 새로 생성될 레포지토리 리스트
        self.is_insert_queue = is_insert_queue

    def update(self):
        # 0. Github API 호출 가능한지 체크
        self.get_rate_remaining()

        # 실제로 github 에 존재하는 user 인지 체크
        user_information: Optional[UserInformationDto] = self.github_adapter.get_user_info(self.username)
        if user_information is None and self.is_insert_queue:
            insert_queue(self.username)
            raise RateLimit()

        # 1. GithubUser 가 있는지 체크, 없으면 생성
        self.github_user: GithubUser = self.get_or_create_github_user(user_information)

        # 2. User 의 repository 정보를 가져온다
        repo_service = RepositoryService(github_user=self.github_user)
        for repository in self.get_user_repository_urls(user_information):
            repo_service.repositories.append(repo_service.create_dto(repository))

        # 3. Organization 정보와 연관된 repository 업데이트
        org_service = OrganizationService(github_user=self.github_user)
        org_service.update_or_create_organization(user_information.organizations_url)
        org_service.get_organization_repository()

        # 4. Repository 정보 업데이트
        repo_service.repositories += org_service.repositories
        repo_service.update_repositories()

        # 5. Language and UserLanguage 업데이트
        repo_service.update_or_create_language()

        return self.update_success(
            total_contribution=repo_service.total_contribution,
            total_stargazers_count=repo_service.total_stargazers_count
        )

    def get_or_create_github_user(self, user_information: UserInformationDto) -> GithubUser:
        try:
            update_fields = ['status']
            github_user = GithubUser.objects.get(username=self.username)
            github_user.status = GithubUser.UPDATING

            for key, value in asdict(user_information).items():
                if key in self.user_update_fields:
                    if getattr(github_user, key, '') != value:
                        setattr(github_user, key, value)
                        update_fields.append(key)

            github_user.save(update_fields=update_fields)

        except GithubUser.DoesNotExist:
            github_user = GithubUser.objects.create(
                username=self.username,
                name=user_information.name,
                email=user_information.email,
                location=user_information.location,
                avatar_url=user_information.avatar_url,
                company=user_information.company,
                bio=user_information.bio,
                blog=user_information.blog,
                public_repos=user_information.public_repos,
                followers=user_information.followers,
                following=user_information.following
            )
            # todo: 비동기 (rabbitMQ)
            SlackService.slack_notify_new_user(github_user)

        return github_user

    def get_user_repository_urls(self, user_information: UserInformationDto) -> list:
        """
        유저가 가지고 있는 repository url 들을 반환
        """
        limit_repository_count = 250
        params = {'per_page': self.github_api_per_page, 'page': 1}
        repositories = []

        for i in range(0, (self.github_user.public_repos // self.github_api_per_page) + 1):
            params['page'] = i + 1
            repositories, status_code = self.github_adapter.get_repository_infos(user_information.repos_url, params)
            repositories.extend(repositories)

        # todo: 레포지토리가 너무 많은경우 한번 프로세스에 async 로 처리하는데 서버 성능이 못따라감.
        #       일단 250개 미만으로 업데이트 하고, 이 부분에 대해서 고민해보기 (일단 리포팅만)
        if len(repositories) > limit_repository_count:
            capture_exception(Exception(f'[Over Repo] {self.github_user.username} - count : {len(repositories)}'))

        return repositories[:limit_repository_count]

    def get_rate_remaining(self) -> int:
        remaining = self.github_adapter.check_rate_limit()

        if remaining <= 0:
            if self.is_insert_queue:
                insert_queue(self.username)
            raise RateLimit()

        return remaining

    def update_success(self, total_contribution: int, total_stargazers_count: int) -> GithubUser:
        """
        유저의 정보들을 최종적으로 업데이트 하는 함수
        """
        self.github_user.status = GithubUser.COMPLETED
        self.github_user.total_contribution = total_contribution
        self.github_user.total_stargazers_count = total_stargazers_count

        is_completed, continuous_count = get_continuous_commit_day(self.github_user.username)
        if is_completed:
            self.github_user.continuous_commit_day = continuous_count

        total_score = self.get_total_score(self.github_user)
        user_rank = self.update_user_ranking(total_score)

        self.github_user.total_score = total_score
        self.github_user.previous_user_rank = self.github_user.user_rank
        self.github_user.user_rank = user_rank
        self.github_user.tier = self.get_tier_statistics(user_rank)
        self.github_user.save(update_fields=[
            'status', 'updated', 'total_contribution', 'total_stargazers_count',
            'tier', 'continuous_commit_day', 'previous_user_rank', 'user_rank', 'total_score'
        ])

        return self.github_user

    @staticmethod
    def get_total_score(github_user: GithubUser) -> int:
        """
        종합 점수 계산 정첵
        기여도 - 15%, 1일1커밋(x10) - 75%, 팔로워 - 5%, 팔로잉 - 5%
        """
        return int(
            github_user.total_contribution * 0.15 +
            github_user.continuous_commit_day * 7.5 +
            github_user.followers * 0.05 +
            github_user.following * 0.05
        )

    @staticmethod
    def get_tier_statistics(user_rank: int) -> int:
        """
        티어 통계 계산 정책
        """
        last_user_rank = GithubUser.objects.order_by('-user_rank').values_list('user_rank', flat=True)[0]
        if not user_rank:
            return GithubUser.UNRANK

        # 챌린저 2%
        if user_rank == 1 or user_rank <= last_user_rank * 0.02:
            tier = GithubUser.CHALLENGER
        # 마스터 2~5%
        elif last_user_rank * 0.02 < user_rank <= last_user_rank * 0.05:
            tier = GithubUser.MASTER
        # 다이아: 5~15%
        elif last_user_rank * 0.05 < user_rank <= last_user_rank * 0.15:
            tier = GithubUser.DIAMOND
        # 플래티넘 15~25%
        elif last_user_rank * 0.15 < user_rank <= last_user_rank * 0.25:
            tier = GithubUser.PLATINUM
        # 골드: 25~35%
        elif last_user_rank * 0.25 < user_rank <= last_user_rank * 0.35:
            tier = GithubUser.GOLD
        # 실버: 35%~60%
        elif last_user_rank * 0.35 < user_rank <= last_user_rank * 0.6:
            tier = GithubUser.SILVER
        # 브론즈: 60~95%
        elif last_user_rank * 0.6 < user_rank <= last_user_rank * 0.95:
            tier = GithubUser.BRONZE
        # 언랭: 95.%~
        else:
            tier = GithubUser.UNRANK

        return tier

    @staticmethod
    def update_user_ranking(total_score: int):
        """
        total score 로 전체 유저의 순위를 계산하는 함수
        """
        return GithubUser.objects.filter(
            total_score__gt=total_score
        ).values('total_score').annotate(Count('id')).count() + 1

    @staticmethod
    def create_dto(user_information_data: dict) -> UserInformationDto:
        return UserInformationDto(**user_information_data)
