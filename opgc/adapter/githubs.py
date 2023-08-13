import json
from enum import Enum
from typing import Optional

import aiohttp
import requests
from django.conf import settings
from furl import furl
from requests import Response

from sentry_sdk import capture_exception

from core.github_dto import UserInformationDto
from utils.exceptions import GitHubUserDoesNotExist, json_handler_manager
from utils.type import convert_dict_key_lower


class RequestMethod(Enum):
    GET = 'get'
    POST = 'post'


class GithubAdapter:
    headers = settings.GITHUB_API_HEADER
    github_url = furl('https://api.github.com/')

    @classmethod
    def _handle_request(
        cls,
        url: str,
        method: RequestMethod,
        params: Optional[dict] = None
    ) -> Optional[Response]:

        try:
            _request = requests.post if method == RequestMethod.POST else requests.get
            res = _request(url, headers=cls.headers, params=params)

        except Exception as e:
            capture_exception(e)
            return None

        return res

    @classmethod
    async def _async_handle_request(
        cls,
        url: str,
        method: RequestMethod,
        params: Optional[dict] = None
    ):
        async with aiohttp.ClientSession() as session:
            if method == RequestMethod.POST:
                async with session.post(url, headers=cls.headers) as res:
                    response_text = await res.text()
            else:
                async with session.get(url, headers=cls.headers, params=params) as res:
                    response_text = await res.text()

        return res, response_text

    @classmethod
    async def get_infos(cls, url):
        return await cls._async_handle_request(url, RequestMethod.GET)

    @classmethod
    def check_rate_limit(cls) -> int:
        """
        현재 호출할 수 있는 Github API rate 체크
        참고: github api 의 경우 token 있는경우 시간당 5000번, 없으면 60번 호출 가능
              https://docs.gitlab.com/ee/user/admin_area/settings/user_and_ip_rate_limits.html#response-headers
        """
        res = cls._handle_request(url=cls.github_url.set(path=f'rate_limit').url, method=RequestMethod.GET)

        if res.status_code != 200:
            # 이 경우는 rate_limit api 가 호출이 안되는건데,
            # 이런경우가 깃헙장애 or rate_limit 호출에 제한이 있는지 모르겟다.
            capture_exception(Exception("Can't get RATE LIMIT."))
            return 0

        try:
            content = json.loads(res.content)
            remaining = content['rate']['remaining']

        except json.JSONDecodeError:
            return 0

        return remaining

    @classmethod
    def get_user_info(cls, username: str) -> Optional[UserInformationDto]:
        """
        깃헙에 해당 유저가 존재하는지 체크
        """
        res = cls._handle_request(url=cls.github_url.set(path=f'/users/{username}').url, method=RequestMethod.GET)

        if res.status_code == 404:
            raise GitHubUserDoesNotExist()
        elif res.status_code != 200:
            return None

        return UserInformationDto(**json.loads(res.content))

    @classmethod
    def get_repository_infos(cls, repos_url: str, params: Optional[dict] = None) -> (Optional[list], int):
        """
        repository 정보를 가져옵니다.
        """
        res = cls._handle_request(url=repos_url, method=RequestMethod.GET, params=params)

        if res.status_code != 200:
            return None, res.status_code

        with json_handler_manager():
            repository_info = json.loads(res.content)

        return repository_info, res.status_code

    @classmethod
    def get_organization_infos(cls, organization_url: str) -> (Optional[list], int):
        """
        organization 정보를 가져옵니다.
        """
        res = cls._handle_request(url=organization_url, method=RequestMethod.GET)

        if res.status_code != 200:
            return None, res.status_code

        with json_handler_manager():
            organization_infos = json.loads(res.content)

        return organization_infos, res.status_code

    @classmethod
    def get_contributor_infos(cls, contributors_url: str, params: dict) -> (Optional[list], int):
        """
        contributor 정보를 가져옵니다.
        """
        res = cls._handle_request(url=contributors_url, method=RequestMethod.GET, params=params)

        if res.status_code != 200:
            return None, res.status_code

        with json_handler_manager():
            contributor_infos = json.loads(res.content)

        return contributor_infos, res.status_code

    @classmethod
    def get_languages(cls, languages_url: str, params: Optional[dict] = None) -> (Optional[dict], int):
        """
        language 정보를 가져옵니다.
        """
        res = cls._handle_request(url=languages_url, method=RequestMethod.GET, params=params)

        if res.status_code != 200:
            return None, res.status_code

        with json_handler_manager():
            languages: dict = convert_dict_key_lower(
                data=json.loads(res.content)
            )

        return languages, res.status_code
