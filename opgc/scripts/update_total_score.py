import timeit

from chunkator import chunkator

from apps.githubs.models import GithubUser
from core.services.github_service import GithubInformationService


def run():
    start_time = timeit.default_timer()  # 시작 시간 체크

    print('------- start update information -------')
    github_users = GithubUser.objects.all()

    for github_user in chunkator(github_users, 1000):
        github_service = GithubInformationService(username=github_user.username)
        github_user.total_score = github_service.get_total_score(github_user)
        github_user.save(update_fields=['total_score'])
        print(f'[{github_user}] - {github_user.total_score}')

    for github_user in chunkator(github_users, 1000):
        github_service = GithubInformationService(username=github_user.username)
        github_user.tier = github_service.get_tier_statistics(github_user.user_rank)
        github_user.save(update_fields=['tier'])
        print(f'[{github_user}] - {github_user.get_tier_display()}[{github_user.user_rank}]')

    print('------- end update information -------')
    terminate_time = timeit.default_timer()  # 종료 시간 체크
    print(f'{terminate_time - start_time:.2f}초 걸렸습니다.')
