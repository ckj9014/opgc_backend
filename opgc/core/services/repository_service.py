import asyncio
import json
from typing import Optional, List

from adapter.githubs import GithubAdapter
from apps.githubs.models import GithubUser, Repository, Language, UserLanguage
from core.github_dto import RepositoryDto, ContributorDto
from utils.exceptions import manage_api_call_fail, REASON_FORBIDDEN


AUTO_COMMIT_REPO_NAME_REGEX = [
    'autoCommit', 'auto-commit', 'auto-green', 'GithubCommitFaker',
    'always_commit_into_git', 'AutoGreen', 'AutoApi', 'GitHubPoster',
    'commit-auto', 'github-auto-green-bot'
]


class RepositoryService:
    github_adapter = GithubAdapter
    github_api_per_page = 50

    def __init__(self, github_user: GithubUser):
        self.github_user = github_user
        self.total_contribution = 0
        self.total_stargazers_count = 0
        self.repositories: List[RepositoryDto] = []  # 업데이트할 레포지토리 리스트
        self.new_repository_list = []  # 새로 생성될 레포지토리 리스트
        self.update_languages = {}  # 업데이트 할 language

    def update_repositories(self) -> bool:
        # 유저의 현재 모든 repository 를 가져온다.
        user_repositories = list(Repository.objects.filter(github_user=self.github_user))

        # loop = asyncio.get_event_loop()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.get_update_repository_futures(self.repositories, user_repositories))

        if self.new_repository_list:
            Repository.objects.bulk_create(self.new_repository_list)

        # 남아 있는 user_repository 는 삭제된 repository 라 DB 에서도 삭제 해준다.
        delete_repository_ids = []
        for repository in user_repositories:
            delete_repository_ids.append(repository.id)

        if delete_repository_ids:
            Repository.objects.filter(id__in=delete_repository_ids).delete()

        return True

    def get_repositories(self, repos_url: str) -> List[RepositoryDto]:
        repositories = []
        repository_infos, status_code = self.github_adapter.get_repository_infos(repos_url)

        if repository_infos is None:
            manage_api_call_fail(self.github_user, status_code)

        for repository_info in repository_infos:
            repository_dto = self.create_dto(repository_info)
            repositories.append(repository_dto)

        return repositories

    def create_repository(self, repository: RepositoryDto) -> (int, Optional[Repository]):
        new_repository = None

        if self.is_fork_repository(repository.fork):
            return 0, None

        contributor = self.check_contributor(repository)

        # contributor 이거나 owner 인 경우
        if contributor.is_contributor or repository.owner.lower() == self.github_user.username.lower():
            new_repository = Repository(
                github_user=self.github_user,
                name=repository.name,
                full_name=repository.full_name,
                owner=repository.owner,
                contribution=contributor.contributions,
                stargazers_count=repository.stargazers_count,
                rep_language=repository.language if repository.language else '',
                languages=contributor.languages
            )

        self.total_stargazers_count += repository.stargazers_count

        return contributor.contributions, new_repository

    def check_contributor(self, repository: RepositoryDto) -> ContributorDto:
        """
        User 가 Repository 의 contributor 인지 확인한다.
        contributions 와 language 확인을 위해 아래 로직을 타야함
        Too many Contributor 403 오류인 경우만 어쩔수 없이 contributions 확인 불가
        """
        params = {'per_page': self.github_api_per_page, 'page': 1}

        for i in range(0, (self.github_user.public_repos // self.github_api_per_page) + 1):
            params['page'] = i + 1
            contributor_infos, status_code = self.github_adapter.get_contributor_infos(
                contributors_url=repository.contributors_url,
                params=params
            )

            if contributor_infos is None:
                fail_type = manage_api_call_fail(self.github_user, status_code)
                if fail_type == REASON_FORBIDDEN:
                    break
                continue

            for contributor in contributor_infos:
                # User 타입이고 contributor 가 본인인 경우 (깃헙에서 대소문자 구분을 하지않아서 lower 처리후 비교)
                if self.is_contributor(contributor, self.github_user.username):
                    contributions = contributor.get('contributions', 0)
                    return ContributorDto(
                        languages=self.record_language(repository.languages_url) if contributions > 0 else '',
                        is_contributor=True,
                        contributions=contributions
                    )

        return ContributorDto(
            languages='',
            is_contributor=False,
            contributions=0
        )

    def record_language(self, languages_url: str) -> str:
        """
        repository 에서 사용중인 언어를 찾아서 dictionary 에 type 과 count 를 저장
        - count : 해당 언어로 작성된 코드의 바이트 수.
        """
        languages, status_code = self.github_adapter.get_languages(languages_url)

        if languages is None:
            manage_api_call_fail(self.github_user, status_code)

        if not languages:
            return ''

        for language_type, count in languages.items():
            if not self.update_languages.get(language_type):
                self.update_languages[language_type] = count
            else:
                self.update_languages[language_type] += count

        return json.dumps(list(languages.keys()))

    def update_or_create_language(self):
        """
        새로 추가된 언어를 만들고 User 가 사용하는 언어사용 count(byte 수)를 업데이트 해주는 함수
        """
        # DB에 없던 Language 생성
        new_language_list = []
        exists_languages = set(Language.objects.filter(
            type__in=self.update_languages.keys()
        ).values_list('type', flat=True))
        new_languages = set(self.update_languages.keys()) - exists_languages

        for language in new_languages:
            new_language_list.append(Language(type=language))

        if new_language_list:
            Language.objects.bulk_create(new_language_list)

        # 기존에 있던 UserLanguage 업데이트
        new_user_languages = []
        user_language_qs = UserLanguage.objects.prefetch_related('language').filter(
            github_user_id=self.github_user.id,
            language__type__in=self.update_languages.keys()
        )

        for user_language in user_language_qs:
            if user_language.language.type in self.update_languages.keys():
                count = self.update_languages.pop(user_language.language.type)

                if user_language.number != count:
                    user_language.number = count
                    user_language.save(update_fields=['number'])

        # 새로운 UserLanguage 생성
        languages = Language.objects.filter(type__in=self.update_languages.keys())
        for language in languages:
            new_user_languages.append(
                UserLanguage(
                    github_user_id=self.github_user.id,
                    language_id=language.id,
                    number=self.update_languages.pop(language.type)
                )
            )

        if new_user_languages:
            UserLanguage.objects.bulk_create(new_user_languages)

    async def update_repository(self, repository: RepositoryDto, user_repositories: list):
        is_exist_repo = False

        for idx, user_repo in enumerate(user_repositories):
            if user_repo.full_name == repository.full_name and user_repo.owner == repository.owner:
                update_fields = []
                is_exist_repo = True
                contribution = 0

                user_repositories.pop(idx)
                res, content = await GithubAdapter.get_infos(repository.contributors_url)

                if res.status == 200:
                    for contributor in json.loads(content):
                        # User 타입이고 contributor 가 본인인 경우 (깃헙에서 대소문자 구분을 하지않아서 lower 처리후 비교)
                        if self.is_contributor(contributor, self.github_user.username):
                            contribution = contributor.get('contributions')
                            self.record_language(repository.languages_url)

                if user_repo.contribution != contribution:
                    user_repo.contribution = contribution
                    update_fields.append('contribution')

                if user_repo.stargazers_count != repository.stargazers_count:
                    user_repo.stargazers_count = repository.stargazers_count
                    update_fields.append('stargazers_count')

                if update_fields:
                    user_repo.save(update_fields=update_fields)

                self.total_stargazers_count += repository.stargazers_count
                self.total_contribution += contribution
                break

        # 새로운 레포지토리인 경우
        if not is_exist_repo:
            _contribution, new_repository = self.create_repository(repository)

            if new_repository:
                self.new_repository_list.append(new_repository)

            self.total_contribution += _contribution

    async def get_update_repository_futures(self, repositories, user_repositories: list):
        futures = [
            asyncio.create_task(
                self.update_repository(repository, user_repositories)
            ) for repository in repositories
        ]

        await asyncio.gather(*futures)

    @staticmethod
    def create_dto(repository_data: dict) -> RepositoryDto:
        return RepositoryDto(**repository_data)

    @staticmethod
    def is_contributor(contributor: dict, github_user_name: str):
        if contributor.get('type') == 'User' and contributor.get('login').lower() == github_user_name.lower():
            return True
        return False

    @staticmethod
    def is_fork_repository(fork: bool):
        """포크한 레포지토리인지 체크"""
        return fork is True

    def has_auto_commit_repository(self) -> bool:
        """
        오토커밋 실행하는 레포지토리가 있는지 체크
        """
        for repository in self.repositories:
            for block_name in AUTO_COMMIT_REPO_NAME_REGEX:
                if repository.name.lower() in block_name.lower():
                    return True
        return False
