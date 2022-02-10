import asyncio
import json
from typing import Optional

import aiohttp
import requests
from django.conf import settings

from apps.githubs.models import GithubUser, Repository, Language, UserLanguage
from core.github_dto import RepositoryDto
from utils.exceptions import manage_api_call_fail, REASON_FORBIDDEN

PER_PAGE = 50


class RepositoryService:

    def __init__(self, github_user: GithubUser):
        self.github_user = github_user
        self.total_contribution = 0
        self.total_stargazers_count = 0
        self.repositories = []  # 업데이트할 레포지토리 리스트
        self.new_repository_list = []  # 새로 생성될 레포지토리 리스트
        self.update_language_dict = {}  # 업데이트할 language

    @staticmethod
    def create_dto(repository_data: dict) -> RepositoryDto:
        return RepositoryDto(**repository_data)

    def update_repositories(self) -> bool:
        """
        레포지토리 업데이트 함수
        """
        # 유저의 현재 모든 repository 를 가져온다.
        user_repositories = list(Repository.objects.filter(github_user=self.github_user))

        # loop = asyncio.get_event_loop()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.update_repository_futures(self.repositories, user_repositories))

        if self.new_repository_list:
            Repository.objects.bulk_create(self.new_repository_list)

        # 남아 있는 user_repository 는 삭제된 repository 라 DB 에서도 삭제 해준다.
        repo_ids = []
        for repo in user_repositories:
            repo_ids.append(repo.id)

        if repo_ids:
            Repository.objects.filter(id__in=repo_ids).delete()

        return True

    def create_repository(self, repository: RepositoryDto) -> (int, Optional[Repository]):
        contribution = 0
        languages = ''
        is_contributor = False
        new_repository = None

        if repository.fork is True:
            return 0, None

        # User 가 Repository 의 contributor 인지 확인한다.
        # contributions 와 language 확인을 위해 아래 로직을 타야함
        # Too many Contributor 403 오류인 경우만 어쩔수 없이 contributions 확인 불가
        params = {'per_page': PER_PAGE, 'page': 1}
        for i in range(0, (self.github_user.public_repos // PER_PAGE) + 1):
            params['page'] = i + 1
            res = requests.get(repository.contributors_url, headers=settings.GITHUB_API_HEADER)

            if res.status_code != 200:
                fail_type = manage_api_call_fail(self.github_user, res.status_code)
                if fail_type == REASON_FORBIDDEN:
                    break
            else:
                try:
                    contributors = json.loads(res.content)
                except json.JSONDecodeError:
                    return contribution, new_repository

                for contributor in contributors:
                    # User 타입이고 contributor 가 본인인 경우 (깃헙에서 대소문자 구분을 하지않아서 lower 처리후 비교)
                    if contributor.get('type') == 'User' and \
                            contributor.get('login').lower() == self.github_user.username.lower():
                        contribution = contributor.get('contributions', 0)

                        if contribution > 0:
                            languages = self.record_language(repository.languages_url)

                        is_contributor = True
                        break

                if is_contributor:
                    break

        if is_contributor or repository.owner.lower() == self.github_user.username.lower():
            # contributor 이거나 owner 인 경우
            new_repository = Repository(
                github_user=self.github_user,
                name=repository.name,
                full_name=repository.full_name,
                owner=repository.owner,
                contribution=contribution,
                stargazers_count=repository.stargazers_count,
                rep_language=repository.language if repository.language else '',
                languages=languages
            )

        self.total_stargazers_count += repository.stargazers_count

        return contribution, new_repository

    def record_language(self, languages_url: str) -> str:
        """
        repository 에서 사용중인 언어를 찾아서 dictionary 에 type 과 count 를 저장
        - count : 해당 언어로 작성된 코드의 바이트 수.
        """

        res = requests.get(languages_url, headers=settings.GITHUB_API_HEADER)
        if res.status_code != 200:
            manage_api_call_fail(self.github_user, res.status_code)

        try:
            languages_data = json.loads(res.content)
        except json.JSONDecodeError:
            return ''

        if languages_data:
            for _type, count in languages_data.items():
                if not self.update_language_dict.get(_type):
                    self.update_language_dict[_type] = count
                else:
                    self.update_language_dict[_type] += count

            return json.dumps(list(languages_data.keys()))

        return ''

    def update_or_create_language(self):
        """
        새로 추가된 언어를 만들고 User 가 사용하는 언어사용 count(byte 수)를 업데이트 해주는 함수
        """

        # DB에 없던 Language 생성
        new_language_list = []
        exists_languages = set(Language.objects.filter(
            type__in=self.update_language_dict.keys()).values_list('type', flat=True)
        )
        new_languages = set(self.update_language_dict.keys()) - exists_languages

        for language in new_languages:
            new_language_list.append(Language(type=language))

        if new_language_list:
            Language.objects.bulk_create(new_language_list)

        # 가존에 있던 UserLanguage 업데이트
        new_user_languages = []
        user_language_qs = UserLanguage.objects.prefetch_related('language').filter(
            github_user_id=self.github_user.id, language__type__in=self.update_language_dict.keys()
        )

        for user_language in user_language_qs:
            if user_language.language.type in self.update_language_dict.keys():
                count = self.update_language_dict.pop(user_language.language.type)

                if user_language.number != count:
                    user_language.number = count
                    user_language.save(update_fields=['number'])

        # 새로운 UserLanguage 생성
        languages = Language.objects.filter(type__in=self.update_language_dict.keys())
        for language in languages:
            new_user_languages.append(
                UserLanguage(
                    github_user_id=self.github_user.id,
                    language_id=language.id,
                    number=self.update_language_dict.pop(language.type)
                )
            )

        if new_user_languages:
            UserLanguage.objects.bulk_create(new_user_languages)

    async def update_repository(self, repository: RepositoryDto, user_repositories: list):  # 코루틴 정의
        is_exist_repo = False

        for idx, user_repo in enumerate(user_repositories):
            if user_repo.full_name == repository.full_name and user_repo.owner == repository.owner:
                is_exist_repo = True
                user_repositories.pop(idx)
                update_fields = []
                contribution = 0

                # User 가 Repository 의 contributor 인지 확인한다.
                async with aiohttp.ClientSession() as session:
                    async with session.get(repository.contributors_url, headers=settings.GITHUB_API_HEADER) as res:
                        response_data = await res.text()
                        response_status = res.status

                if response_status == 200:
                    for contributor in json.loads(response_data):
                        # User 타입이고 contributor 가 본인인 경우 (깃헙에서 대소문자 구분을 하지않아서 lower 처리후 비교)
                        if contributor.get('type') == 'User' and \
                                contributor.get('login').lower() == self.github_user.username.lower():
                            contribution = contributor.get('contributions')
                            # languages number update
                            self.record_language(repository.languages_url)

                # repository update
                if user_repo.contribution != contribution:
                    user_repo.contribution = contribution
                    update_fields.append('contribution')

                # repository update
                if user_repo.stargazers_count != repository.stargazers_count:
                    user_repo.stargazers_count = repository.stargazers_count
                    update_fields.append('stargazers_count')

                if update_fields:
                    user_repo.save(update_fields=update_fields)

                self.total_stargazers_count += repository.stargazers_count
                self.total_contribution += contribution
                break

        # 새로운 레포지토리
        if not is_exist_repo:
            _contribution, new_repository = self.create_repository(repository)

            if new_repository:
                self.new_repository_list.append(new_repository)

            self.total_contribution += _contribution

    async def update_repository_futures(self, repositories, user_repositories: list):
        futures = [
            asyncio.ensure_future(self.update_repository(repository, user_repositories)) for repository in repositories
        ]

        await asyncio.gather(*futures)
