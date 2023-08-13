from dataclasses import asdict
import pytest

from api.exceptions import BlockedUser, NotUserType
from apps.githubs.models import BlockUser, GithubUser
from core.github_dto import UserType
from core.services.github_service import GithubInformationService
from tests.utils.dto_factory import UserInformationDTOFactory
from tests.utils.model_factory import GithubUserFactory


@pytest.mark.django_db
class TestGithubInformationService:

    def setup_class(self):
        self.username = 'JAY-Chan9yu'

    def test_등록되지_않은_유저정보를_통해_get_or_create_github_user_호출시_신규유저가_생성된다(self):
        user_information_dto = UserInformationDTOFactory.create()
        github_information_service = GithubInformationService(username=self.username)
        github_user = github_information_service.get_or_create_github_user(user_information_dto)

        assert github_user is not None
        for key, value in asdict(user_information_dto).items():
            if key in github_information_service.user_update_fields:
                assert getattr(github_user, key, '') == value

    @pytest.mark.django_db
    def test_블락된_유저인_경우_get_or_create_github_user_호출시_BlockedUser_익셉션이_발생된다(self):
        # 특정유저 블락
        BlockUser.objects.create(username=self.username)

        user_information_dto = UserInformationDTOFactory.create()
        github_information_service = GithubInformationService(username=self.username)

        with pytest.raises(BlockedUser):
            github_information_service.get_or_create_github_user(user_information_dto)

    @pytest.mark.django_db
    def test_타입이_user_가_아닌_경우_get_or_create_github_user_호출시_NotUserType_익셉션이_발생된다(self):
        user_information_dto = UserInformationDTOFactory.create(type=UserType.organization)
        github_information_service = GithubInformationService(username=self.username)

        with pytest.raises(NotUserType):
            github_information_service.get_or_create_github_user(user_information_dto)

    @pytest.mark.django_db
    def test_이미_존재하는_유저일때_get_or_create_github_user_호출시_유저정보가_업데이트_된다(self):
        GithubUserFactory.create(username=self.username)
        exists_user = GithubUser.objects.get(username=self.username)
        assert exists_user.followers == 0
        assert exists_user.following == 0
        assert exists_user.company == ""
        assert exists_user.status == GithubUser.NONE

        update_data = {
            "followers": 10,
            "following": 100,
            "company": "benz"
        }

        user_information_dto = UserInformationDTOFactory.create(**update_data)
        github_information_service = GithubInformationService(username=self.username)
        updated_user = github_information_service.get_or_create_github_user(user_information_dto)

        assert updated_user.id == exists_user.id
        assert updated_user.followers == update_data["followers"]
        assert updated_user.following == update_data["following"]
        assert updated_user.company == update_data["company"]
        assert updated_user.status == GithubUser.UPDATING
