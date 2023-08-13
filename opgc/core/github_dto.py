from dataclasses import dataclass
from enum import Enum


class UserType(Enum):
    user = 'User'
    organization = 'Organization'


@dataclass
class UserInformationDto:
    name: str  # 이름
    type: UserType
    email: str  # 이메일
    location: str  # 국가
    avatar_url: str  # 프로필 URL
    company: str  # 회사
    bio: str  # 설명
    blog: str  # 블로그
    public_repos: int
    followers: int
    following: int
    repos_url: str
    organizations_url: str

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.email = kwargs.get('email')
        self.location = kwargs.get('location')
        self.avatar_url = kwargs.get('avatar_url')
        self.company = kwargs.get('company')
        self.bio = kwargs.get('bio')
        self.blog = kwargs.get('blog')
        self.public_repos = kwargs.get('public_repos')
        self.followers = kwargs.get('followers')
        self.following = kwargs.get('following')
        self.repos_url = kwargs.get('repos_url')
        self.organizations_url = kwargs.get('organizations_url')
        self.type = UserType(kwargs.get('type'))


@dataclass
class OrganizationDto:
    name: str  # organization 네임
    description: str  # 설명
    logo: str  # 프로필(로고)
    repos_url: str  # repository URL

    def __init__(self, **kwargs):
        self.name = kwargs.get('login', '')
        self.description = kwargs.get('description', '')
        self.logo = kwargs.get('avatar_url', '')
        self.repos_url = kwargs.get('repos_url', '')


@dataclass
class RepositoryDto:
    name: str  # 레포지토리 네임
    full_name: str  # 레포지토리 풀네임
    owner: str  # 소유자(?)
    stargazers_count: int  # start 카운트
    fork: bool  # fork 여부
    language: str  # 대표 언어
    contributors_url: str  # contributor 정보 URL
    languages_url: str  # 언어 정보 URL

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.full_name = self._set_repository_full_name(kwargs.get('full_name'))
        self.owner = kwargs.get('owner').get('login')
        self.stargazers_count = kwargs.get('stargazers_count')
        self.fork = kwargs.get('fork')
        self.language = kwargs.get('language', '')
        self.contributors_url = kwargs.get('contributors_url')
        self.languages_url = kwargs.get('languages_url')

    @staticmethod
    def _set_repository_full_name(full_name: str) -> str:
        return full_name if len(full_name) < 490 else f"{full_name[:490]}..."


@dataclass
class ContributorDto:
    languages: str
    is_contributor: bool
    contributions: int
