import json
from dataclasses import asdict

import requests
from django.conf import settings
from django.db.models import Count
from furl import furl
from sentry_sdk import capture_exception

from apps.githubs.models import GithubUser
from core.github_dto import UserInformationDto
from utils.exceptions import GitHubUserDoesNotExist, RateLimit, manage_api_call_fail, insert_queue
from core.organization_service import OrganizationService
from core.repository_service import RepositoryService
from utils.github import get_continuous_commit_day
from utils.slack import slack_notify_new_user

FURL = furl('https://api.github.com/')
GITHUB_RATE_LIMIT_URL = 'https://api.github.com/rate_limit'
PER_PAGE = 50
CHECK_RATE_REMAIN = 0
USER_UPDATE_FIELDS = [
    'avatar_url', 'company', 'bio', 'blog', 'public_repos', 'followers', 'following', 'name', 'email', 'location'
]


class GithubInformationService:
    """
    Authorization - access token 이 있는경우 1시간에 5000번 api 호출 가능 없으면 60번
    """

    github_user = None

    def __init__(self, username, is_30_min_script=False):
        self.username = username
        self.new_repository_list = []  # 새로 생성될 레포지토리 리스트
        self.update_language_dict = {}  # 업데이트할 language
        self.is_30_min_script = is_30_min_script

    @staticmethod
    def create_dto(user_information_data: dict) -> UserInformationDto:
        return UserInformationDto(**user_information_data)

    def check_github_user(self) -> UserInformationDto:
        """
        Github User 정보를 가져오거나 생성하는 함수
        """
        user_api = FURL.set(path=f'/users/{self.username}').url
        res = requests.get(user_api, headers=settings.GITHUB_API_HEADER)

        if res.status_code == 404:
            raise GitHubUserDoesNotExist()
        elif res.status_code != 200:
            manage_api_call_fail(self.github_user, res.status_code)

        return self.create_dto(json.loads(res.content))

    def get_or_create_github_user(self, user_information: UserInformationDto) -> GithubUser:
        try:
            update_fields = ['status']
            github_user = GithubUser.objects.get(username=self.username)
            github_user.status = GithubUser.UPDATING

            for key, value in asdict(user_information).items():
                if key in USER_UPDATE_FIELDS:
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
            slack_notify_new_user(github_user)

        return github_user

    def check_rete_limit(self) -> int:
        # 현재 호출할 수 있는 rate 체크 (token 있는경우 1시간당 5000번 없으면 60번 호출)
        res = requests.get(GITHUB_RATE_LIMIT_URL, headers=settings.GITHUB_API_HEADER)

        if res.status_code != 200:
            # 이 경우는 rate_limit api 가 호출이 안되는건데,
            # 이런경우가 깃헙장애 or rate_limit 호출에 제한이 있는지 모르겟다.
            if not self.is_30_min_script:
                insert_queue(self.username)
            capture_exception(Exception("Can't get RATE LIMIT."))

        # 참고: https://docs.gitlab.com/ee/user/admin_area/settings/user_and_ip_rate_limits.html#response-headers
        # 왠만하면 100 이상 호출하는 경우가 있어서 100으로 지정
        try:
            content = json.loads(res.content)
            remaining = content['rate']['remaining']

            if remaining <= CHECK_RATE_REMAIN:
                if not self.is_30_min_script:
                    insert_queue(self.username)
                raise RateLimit()

        except json.JSONDecodeError:
            return 0

        return remaining

    def update_success(self, total_contribution: int, total_stargazers_count: int) -> GithubUser:
        """
            업데이트 성공 처리
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
        self.github_user.user_rank = user_rank
        self.github_user.tier = self.get_tier_statistics(user_rank)
        self.github_user.save(update_fields=[
            'status', 'updated', 'total_contribution', 'total_stargazers_count',
            'tier', 'continuous_commit_day', 'user_rank', 'total_score'
        ])

        return self.github_user

    @staticmethod
    def get_total_score(github_user: GithubUser) -> int:
        # 기여도 - 15%, 1일1커밋(x10) - 75%, 팔로워 - 5%, 팔로잉 - 5%
        return int(
            github_user.total_contribution * 0.15 +
            github_user.continuous_commit_day * 7.5 +
            github_user.followers * 0.05 +
            github_user.following * 0.05
        )

    @staticmethod
    def get_tier_statistics(user_rank: int) -> int:
        """
            - 티어 통계
            챌린저 2%
            마스터 2~5%
            다이아: 5~15%
            플래티넘 15~25%
            골드: 25~35%
            실버: 35%~60%
            브론즈: 60~95%
            언랭: 95.%~
        """

        last_user_rank = GithubUser.objects.order_by('-user_rank').values_list('user_rank', flat=True)[0]
        if not user_rank:
            return GithubUser.UNRANK

        if user_rank == 1 or user_rank <= last_user_rank * 0.02:
            tier = GithubUser.CHALLENGER
        elif last_user_rank * 0.02 < user_rank <= last_user_rank * 0.05:
            tier = GithubUser.MASTER
        elif last_user_rank * 0.05 < user_rank <= last_user_rank * 0.15:
            tier = GithubUser.DIAMOND
        elif last_user_rank * 0.15 < user_rank <= last_user_rank * 0.25:
            tier = GithubUser.PLATINUM
        elif last_user_rank * 0.25 < user_rank <= last_user_rank * 0.35:
            tier = GithubUser.GOLD
        elif last_user_rank * 0.35 < user_rank <= last_user_rank * 0.6:
            tier = GithubUser.SILVER
        elif last_user_rank * 0.6 < user_rank <= last_user_rank * 0.95:
            tier = GithubUser.BRONZE
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

    def update(self):
        # 0. Github API 호출 가능한지 체크
        self.check_rete_limit()

        # 실제로 github 에 존재하는 user 인지 체크
        user_information: UserInformationDto = self.check_github_user()

        # 1. GithubUser 가 있는지 체크, 없으면 생성
        self.github_user: GithubUser = self.get_or_create_github_user(user_information)

        # 2. User 의 repository 정보를 가져온다
        params = {'per_page': PER_PAGE, 'page': 1}
        repositories = []
        for i in range(0, (self.github_user.public_repos // PER_PAGE) + 1):
            params['page'] = i + 1
            repo_res = requests.get(user_information.repos_url, headers=settings.GITHUB_API_HEADER, params=params)
            repositories.extend(json.loads(repo_res.content))

        repo_service = RepositoryService(github_user=self.github_user)

        try:
            # todo: 레포지토리가 너무 많은경우 한번 프로세스에 async 로 처리하는데 서버 성능이 못따라감.
            #       일단 250개 미만으로 업데이트 하고, 이 부분에 대해서 고민해보기 (일단 리포팅만)
            if len(repositories) > 250:
                capture_exception(Exception(f'[Over Repo] {self.github_user.username} - count : {len(repositories)}'))

            for repository in repositories[:250]:
                repository_dto = repo_service.create_dto(repository)
                repo_service.repositories.append(repository_dto)

        except json.JSONDecodeError:
            pass

        # 3. Organization 정보와 연관된 repository 업데이트
        org_service = OrganizationService(github_user=self.github_user)
        org_service.update_organization(user_information.organizations_url)
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
