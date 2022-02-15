import pytest

from core.services.organization_service import OrganizationService, OrganizationDto


@pytest.mark.django_db
def test_create_org_dto(github_context):

    org_service = OrganizationService(github_context.test_github_user)
    org_dto = org_service.create_dto(github_context.org_dummy_data)

    assert isinstance(org_dto, OrganizationDto)
