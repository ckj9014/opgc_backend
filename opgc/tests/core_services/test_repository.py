import pytest

from core.services.repository_service import RepositoryService, RepositoryDto


@pytest.mark.django_db
def test_create_org_dto(github_context):

    repo_service = RepositoryService(github_context.test_github_user)
    repo_dto = repo_service.create_dto(github_context.repo_dummy_data)

    assert isinstance(repo_dto, RepositoryDto)
