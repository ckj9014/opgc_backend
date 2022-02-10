import asyncio
import timeit

from chunkator import chunkator

from apps.githubs.models import GithubUser
from core.github_service import GithubInformationService
from utils.github import get_continuous_commit_day, is_exists_github_users
from utils.slack import slack_update_1day_1commit


async def update_continuous_commit_day(github_user: GithubUser):
    """
        1일 1커밋 크롤링으로 업데이트
    """
    if not is_exists_github_users(github_user.username):
        return

    is_completed, continuous_count = get_continuous_commit_day(github_user.username)

    if is_completed:
        github_user.continuous_commit_day = continuous_count
        github_user.total_score = GithubInformationService.get_total_score(github_user)
        github_user.save(update_fields=['continuous_commit_day', 'total_score'])


def update_1day_1commit():

    async def update_1day_1commit_futures():
        github_users = GithubUser.objects.all()

        if not github_users:
            return

        futures = [asyncio.ensure_future(update_continuous_commit_day(github_user))
                   for github_user in chunkator(github_users, 1000)]

        await asyncio.gather(*futures)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(update_1day_1commit_futures())


def run():
    start_time = timeit.default_timer()  # 시작 시간 체크
    slack_update_1day_1commit(status='시작🌱', message='')

    update_1day_1commit()

    terminate_time = timeit.default_timer()  # 종료 시간 체크
    slack_update_1day_1commit(
        status='완료🌿',
        message=f'1일 1커밋 카운트 업데이트가 {terminate_time - start_time:.2f}초 걸렸습니다.😎',
    )
