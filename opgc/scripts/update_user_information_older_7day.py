"""
    업데이트 한지 7일이 지난 유저들 업데이트 배치 스크립트
    : 일단 유저 적을때는 매일 새벽에 돌리도록(3,4,5)
"""
import concurrent.futures
import timeit
from dataclasses import asdict
from datetime import datetime, timedelta

from chunkator import chunkator

from apps.githubs.models import GithubUser
from utils.exceptions import RateLimit, insert_queue, GitHubUserDoesNotExist
from core.github_service import GithubInformationService, USER_UPDATE_FIELDS
from utils.github import get_continuous_commit_day
from utils.slack import slack_notify_update_fail, slack_update_older_week_user


def update_github_basic_information(github_user: GithubUser):
    # todo: 유틸쪽으로 분리하기
    github_information_service = GithubInformationService(github_user.username)
    user_information = github_information_service.check_github_user()

    for key, value in asdict(user_information).items():
        if key in USER_UPDATE_FIELDS:
            if getattr(github_user, key, '') != value:
                setattr(github_user, key, value)

    github_user.continuous_commit_day = get_continuous_commit_day(github_user.username)
    github_user.total_score = github_information_service.get_total_score(github_user)
    github_user.user_rank = github_information_service.update_user_ranking(github_user.total_score)
    github_user.tier = github_information_service.get_tier_statistics(github_user.user_rank)
    github_user.save()


def run():
    # 1. 스크립트를 시작하기전 rate_limit 를 체크한다.
    try:
        rate_limit_check_service = GithubInformationService(None)
        rate_limit_check_service.check_rete_limit()

    except RateLimit:
        return

    older_week_date = datetime.now() - timedelta(7)
    github_user_qs = GithubUser.objects.filter(updated__lte=older_week_date)

    if not github_user_qs:
        return

    start_time = timeit.default_timer()  # 시작 시간 체크
    slack_update_older_week_user(status='시작', message='')

    update_user_count = 0
    is_rate_limit = False

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # max_worker default = min(32, os.cpu_count() + 4)
        for github_user in chunkator(github_user_qs, 1000):
            if is_rate_limit:
                insert_queue(username=github_user.username)
                continue

            try:
                # 모든 정보를 업데이트 하지 않고, 유저의 기본정보만 업데이트 한다.
                executor.submit(update_github_basic_information, github_user)
                update_user_count += 1

            except RateLimit:  # rate limit 면 다른 유저들도 업데이드 못함
                slack_notify_update_fail(
                    message=f'Rate Limit 로 인해 업데이트가 실패되었습니다. {update_user_count}명만 업데이트 되었습니다.😭'
                )
                is_rate_limit = True

            except GitHubUserDoesNotExist:
                continue

    remaining = rate_limit_check_service.check_rete_limit()
    terminate_time = timeit.default_timer()  # 종료 시간 체크
    slack_update_older_week_user(
        status='완료',
        message=f'업데이트가 {terminate_time - start_time:.2f}초 걸렸습니다. 🤩 API 호출 남은 횟수 : {remaining}',
        update_user=update_user_count
    )
