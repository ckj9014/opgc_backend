from dataclasses import asdict
from unittest import mock

import pytest
from core.services.github_service import GithubInformationService, UserInformationDto


@pytest.fixture(scope='function')
def mock_slack_notify_new_user():
    with mock.patch('utils.slack.slack_notify_new_user') as patch:
        yield patch


@pytest.mark.django_db
def test_get_or_create_github_user(github_context, mock_slack_notify_new_user):
    username = 'JAY-Chan9yu'
    user_information_dto = UserInformationDto(
        name='jay', email='jay@test.com', location='Republic of Korea', company='DirtyBoyz',
        avatar_url='https://avatars.githubusercontent.com/u/24591259?v=4',
        bio='', blog='', public_repos=0, followers=0, following=0,
        repos_url='', organizations_url=''
    )
    github_information_service = GithubInformationService(username=username)
    github_user = github_information_service.get_or_create_github_user(user_information_dto)

    assert github_user is not None
    for key, value in asdict(user_information_dto).items():
        if key in github_information_service.user_update_fields:
            assert getattr(github_user, key, '') == value
