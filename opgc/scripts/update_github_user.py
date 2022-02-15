from apps.githubs.models import GithubUser
from core.services.github_service import GithubInformationService


def run():
    username = input("input delete username: ")

    try:
        GithubUser.objects.get(username=username)
        github_information_service = GithubInformationService(username=username)
        github_information_service.update()

    except GithubUser.DoesNotExist:
        pass
