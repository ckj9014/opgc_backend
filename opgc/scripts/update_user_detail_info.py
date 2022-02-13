import concurrent.futures
import timeit
from datetime import datetime, timedelta

from chunkator import chunkator

from apps.githubs.models import GithubUser
from utils.exceptions import RateLimit, GitHubUserDoesNotExist
from core.github_service import GithubInformationService
from utils.slack import slack_update_older_week_user, slack_notify_update_fail


def run():
    """
    업데이트가 늦은 날짜 순으로 ordering 된 유저들의 상세 깃헙 정보 업데이트
    (업데이트 한지 일주일 이내 유저 제외)
    rate limit 를 고려하여 새벽 시간대에만 돌림
    """
    try:
        # 1스크립트를 시작하기전 rate_limit 를 체크한다.
        rate_limit_check_service = GithubInformationService(None)
        rate_limit_check_service.check_rete_limit()

    except RateLimit:
        return

    github_user_qs = GithubUser.objects.filter(
        updated__lte=datetime.now() - timedelta(7)
    ).order_by('updated')

    if not github_user_qs:
        return

    start_time = timeit.default_timer()
    slack_update_older_week_user(status='시작', message='')
    update_user_count = 0

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for github_user in chunkator(github_user_qs, 1000):
            try:
                github_information_service = GithubInformationService(github_user.username)
                executor.submit(github_information_service.update)
                update_user_count += 1

            except RateLimit:
                slack_notify_update_fail(
                    message=f'Rate Limit 로 인해 업데이트가 실패되었습니다. '
                            f'{update_user_count}명만 업데이트 되었습니다.😭'
                )
                break

            except GitHubUserDoesNotExist:
                continue

    terminate_time = timeit.default_timer()
    slack_update_older_week_user(
        status='완료',
        message=f'업데이트가 {terminate_time - start_time:.2f}초 걸렸습니다. '
                f'🤖 API 호출 남은 횟수 : {rate_limit_check_service.check_rete_limit()}',
        update_user=update_user_count
    )
