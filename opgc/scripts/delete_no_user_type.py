from adapter.githubs import GithubAdapter
from apps.githubs.models import GithubUser
from apps.reservations.models import UpdateUserQueue
from core.github_dto import UserInformationDto, UserType


def run():
    github_users = GithubUser.objects.all()

    for github_user in github_users:
        try:
            user_information: UserInformationDto = GithubAdapter.get_user_info(github_user.username)

            if user_information.type != UserType.user:
                github_user.delete()
                UpdateUserQueue.objects.filter(username=github_user.username).delete()
                print(f'{github_user.username} 삭제({user_information.type})')

        except Exception:
            pass
