import timeit

from chunkator import chunkator
from sentry_sdk import capture_exception

from apps.reservations.models import UpdateUserQueue
from utils.exceptions import RateLimit
from core.github_service import GithubInformationService
from utils.slack import slack_update_github_user, slack_notify_update_fail


def run():
    """
    30분마다 실행되는 Github user 업데이트
    : github api가 rate_limit 걸려서 더이상 호출하지 못하는 경우
    """
    start_time = timeit.default_timer()  # 시작 시간 체크

    update_user_queue_qs = UpdateUserQueue.objects.filter(
        status__in=[UpdateUserQueue.READY, UpdateUserQueue.FAIL]
    )
    if not update_user_queue_qs:
        return

    try:
        # 스크립트를 시작하기전 rate_limit 를 체크한다.
        rate_limit_check_service = GithubInformationService(is_insert_queue=False)
        rate_limit_check_service.check_rete_limit()

    except RateLimit:
        return

    slack_update_github_user(status='시작', message='')
    update_user_count = 0

    for user_queue in chunkator(update_user_queue_qs, 1000):
        try:
            github_information_service = GithubInformationService(user_queue.username, False)
            github_information_service.update()
            user_queue.status = UpdateUserQueue.SUCCESS
            user_queue.save(update_fields=['status'])
            update_user_count += 1

        except RateLimit:
            # rate limit 면 다른 유저들도 업데이드 못함
            slack_notify_update_fail(
                message=f'Rate Limit 로 인해 업데이트가 실패되었습니다. '
                        f'{update_user_count}명만 업데이트 되었습니다.😭'
            )
            break

        except Exception as e:
            capture_exception(e)

    terminate_time = timeit.default_timer()  # 종료 시간 체크
    slack_update_github_user(
        status='완료',
        message=f'업데이트가 {terminate_time - start_time:.2f}초 걸렸습니다.',
        update_user=update_user_count
    )
