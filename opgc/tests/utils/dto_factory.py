from core.github_dto import UserInformationDto, UserType
from test_helper.factories import DTOFactory


class UserInformationDTOFactory(DTOFactory):
    dto = UserInformationDto
    default_data = {
        "name": "test_name",
        "type": UserType.user,
        "email": "test@test.com",
        "location": "Republic of Korea",
        "avatar_url": "",
        "company": "",
        "bio": "",
        "blog": "",
        "public_repos": 0,
        "followers": 0,
        "following": 0,
        "repos_url": "",
        "organizations_url": ""
    }
