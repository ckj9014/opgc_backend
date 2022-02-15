import pytest

# from test_helper.init_data import InitTestData
from apps.githubs.models import GithubUser


@pytest.fixture(scope='function')
def github_context():
    # init_data = InitTestData()
    test_github_user = GithubUser.objects.create(
        username='test_username',
        name='test_name',
        email='test@test.com',
        location='ROK',
        avatar_url='',
        company='',
        bio='',
        blog='',
        public_repos=0,
        followers=0,
        following=0,
        continuous_commit_day=0
    )

    org_dummy_data = {
        'login': 'jay',
        'description': 'this is dummy data',
        'avatar_url': 'https://test.com',
        'repos_url': 'https://test.com',
    }

    repo_dummy_data = {
        'name': 'test_repo',
        'full_name': 'jay/test_repo',
        'owner': {'login': 'jay'},
        'stargazers_count': 0,
        'fork': False,
        'language': 'python',
        'contributors_url': '',
        'languages_url': '',
    }

    ret = type(
        'context',
        (),
        {
            'org_dummy_data': org_dummy_data,
            'test_github_user': test_github_user,
            'repo_dummy_data': repo_dummy_data
        }
    )

    return ret
