from apps.githubs.models import GithubUser
from core.services.github_service import GithubInformationService
from utils.github import get_continuous_commit_day


def run():
    username = input("input username: ")

    try:
        github_user = GithubUser.objects.get(username=username)
        github_information_service = GithubInformationService(username=username)
        github_information_service.update()

        is_completed, continuous_count = get_continuous_commit_day(username)

        if is_completed:
            github_user.continuous_commit_day = continuous_count
            github_user.total_score = GithubInformationService.get_total_score(github_user)
            github_user.save(update_fields=['continuous_commit_day', 'total_score'])

    except GithubUser.DoesNotExist:
        pass
