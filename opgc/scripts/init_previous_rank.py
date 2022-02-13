from chunkator import chunkator

from apps.githubs.models import GithubUser


def run():

    try:
        github_users = GithubUser.objects.all()
        for github_user in chunkator(github_users, 1000):
            github_user.previous_user_rank = github_user.user_rank
            github_user.save(update_fields=['previous_user_rank'])

    except:
        pass
