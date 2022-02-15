from dataclasses import dataclass


@dataclass
class UserInformationDto:
    name: str  # 이름
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


@dataclass
class OrganizationDto:
    name: str  # organization 네임
    description: str  # 설명
    logo: str  # 프로필(로고)
    repos_url: str  # repository URL

    def __init__(self, name: str, description: str, logo: str, repos_url: str):
        self.name = name
        self.description = description or ''
        self.logo = logo or ''
        self.repos_url = repos_url or ''


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
        self.full_name = kwargs.get('full_name')
        self.owner = kwargs.get('owner').get('login')
        self.stargazers_count = kwargs.get('stargazers_count')
        self.fork = kwargs.get('fork')
        self.language = kwargs.get('language', '')
        self.contributors_url = kwargs.get('contributors_url')
        self.languages_url = kwargs.get('languages_url')


@dataclass
class ContributorDto:
    languages: str
    is_contributor: bool
    contributions: int
