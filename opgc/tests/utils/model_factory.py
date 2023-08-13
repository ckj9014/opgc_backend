from apps.githubs.models import GithubUser
from test_helper.factories import ModelFactory


class GithubUserFactory(ModelFactory):
    model = GithubUser
    default_data = {
        "username": "jay",
        "name": "test_name",
        "email": "test@test.com",
        "location": "Republic of Korea",
        "avatar_url": "",
        "company": "",
        "bio": "",
        "blog": "",
        "public_repos": 0,
        "followers": 0,
        "following": 0,
        "continuous_commit_day": 0,
    }
