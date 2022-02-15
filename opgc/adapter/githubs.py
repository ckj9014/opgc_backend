import json
from enum import Enum
from typing import Optional

import requests
from django.conf import settings
from furl import furl
from requests import Response

from sentry_sdk import capture_exception

from core.github_dto import UserInformationDto
from utils.exceptions import GitHubUserDoesNotExist, RateLimit


class RequestMethod(Enum):
    GET = 'get'
    POST = 'post'


class GithubAdapter:
    headers = settings.GITHUB_API_HEADER
    github_url = furl('https://api.github.com/')

    @classmethod
    def _handle_request(cls, method: RequestMethod, path: str, params: Optional[dict] = None) -> Optional[Response]:

        try:
            _request = requests.post if method == RequestMethod.POST else requests.get
            user_api = cls.github_url.set(path=path).url
            res = _request(user_api, headers=cls.headers, params=params)

        except Exception as e:
            capture_exception(e)
            return None

        return res

    @classmethod
    def check_rate_limit(cls) -> int:
        """
        현재 호출할 수 있는 Github API rate 체크
        참고: github api 의 경우 token 있는경우 시간당 5000번, 없으면 60번 호출 가능
              https://docs.gitlab.com/ee/user/admin_area/settings/user_and_ip_rate_limits.html#response-headers
        """
        res = cls._handle_request(path=f'rate_limit', method=RequestMethod.GET)

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
        res = cls._handle_request(path=f'/users/{username}', method=RequestMethod.GET)

        if res.status_code == 404:
            raise GitHubUserDoesNotExist()
        elif res.status_code != 200:
            return None

        return UserInformationDto(**json.loads(res.content))

    @classmethod
    def get_repository_info(cls, repos_url: str, params: dict) -> dict:
        """
        레포지토리 정보를 가져옵니다.
        """
        res = cls._handle_request(path=repos_url, method=RequestMethod.GET, params=params)
        return json.loads(res.content)
