import concurrent.futures
import timeit
from dataclasses import asdict
from datetime import datetime, timedelta

from chunkator import chunkator

from apps.githubs.models import GithubUser
from utils.exceptions import RateLimit, GitHubUserDoesNotExist
from core.services.github_service import GithubInformationService
from utils.slack import SlackService


def update_github_basic_information(github_user: GithubUser):
    github_information_service = GithubInformationService(github_user.username)
    user_information = github_information_service.github_adapter.get_user_info(github_user.username)

    for key, value in asdict(user_information).items():
        if key in github_information_service.user_update_fields:
            if getattr(github_user, key, '') != value:
                setattr(github_user, key, value)

    # is_completed, continuous_count = get_continuous_commit_day(github_user.username)
    # if is_completed:
    #     github_user.continuous_commit_day = continuous_count

    github_user.total_score = github_information_service.get_total_score(github_user)
    github_user.user_rank = github_information_service.update_user_ranking(github_user.total_score, github_user)
    github_user.tier = github_information_service.get_tier_statistics(github_user.user_rank)
    github_user.save(update_fields=['total_score', 'user_rank', 'tier'])


def run():
    """
    기본적으로 업데이트 되야할 유저 기본정보 업데이트
    (업데이트 한지 일주일 이내 유저 제외)
    """
    try:
        # 스크립트를 시작하기전 rate_limit 를 체크한다.
        rate_limit_check_service = GithubInformationService(is_insert_queue=False)
        rate_limit_check_service.get_rate_remaining()

    except RateLimit:
        return

    github_user_qs = GithubUser.objects.filter(updated__lte=datetime.now() - timedelta(7))

    if not github_user_qs:
        return

    start_time = timeit.default_timer()
    SlackService.slack_update_basic_info(status='시작', message='')
    update_user_count = 0

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # max_worker default = min(32, os.cpu_count() + 4)
        for github_user in chunkator(github_user_qs, 1000):
            try:
                executor.submit(update_github_basic_information, github_user)
                update_user_count += 1

            except RateLimit:
                SlackService.slack_notify_update_fail(
                    message=f'Rate Limit 로 인해 업데이트가 실패되었습니다. '
                            f'{update_user_count}명만 업데이트 되었습니다.😭'
                )

            except GitHubUserDoesNotExist:
                continue

    terminate_time = timeit.default_timer()
    SlackService.slack_update_basic_info(
        status='완료',
        message=f'업데이트가 {terminate_time - start_time:.2f}초 걸렸습니다. '
                f'🤖 API 호출 남은 횟수 : {rate_limit_check_service.get_rate_remaining()}',
        update_user=update_user_count
    )
