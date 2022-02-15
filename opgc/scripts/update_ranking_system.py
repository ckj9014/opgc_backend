import timeit

from chunkator import chunkator
from django.db import transaction
from sentry_sdk import capture_exception

from apps.githubs.models import GithubUser, Language, UserLanguage
from apps.ranks.models import UserRank
from core.services.github_service import GithubInformationService
from utils.exceptions import GitHubUserDoesNotExist
from utils.slack import slack_update_ranking_system


RANK_TYPES = [
    'total_score', 'continuous_commit_day', 'total_contribution', 'total_stargazers_count', 'followers', 'following'
]


class RankService(object):
    # todo: 현재는 데이터가 별로 없어서 order by를 했는데, 더 좋은 아이디어가 있는지 확인 필요!
    #       동점자 처리 어떻게 할지 고민해봐야함!

    def run(self):
        """
        전체 업데이트를 실행을 관리하는 run 함수
        """
        self.update_rank_for_each_type()
        self.update_language_rank()
        self.update_user_ranking()

    @staticmethod
    def update_rank_for_each_type():
        user_fields = [field.name for field in GithubUser._meta.get_fields()]
        for rank_type in RANK_TYPES:
            if rank_type not in user_fields:
                continue

            github_user_data = GithubUser.objects.values('id', rank_type).order_by(f'-{rank_type}')[:100]
            with transaction.atomic():  # 랭킹 업데이트 도중 하나라도 오류가 나면 원상복구
                for order, data in enumerate(github_user_data):
                    user_rank, is_created = UserRank.objects.get_or_create(
                        type=rank_type,
                        ranking=order+1
                    )
                    user_rank.github_user_id = data.get('id')
                    user_rank.score = data.get(rank_type)
                    user_rank.save(update_fields=['github_user_id', 'score'])

    @staticmethod
    def update_language_rank():
        """
        언어별 count 값으로 랭킹
        랭킹 업데이트 도중 하나라도 오류가 나면 원상복구
        """
        for language in chunkator(Language.objects.all(), 1000):
            user_languages = UserLanguage.objects.filter(language_id=language.id).order_by('-number')[:10]

            with transaction.atomic():  # 랭킹 업데이트 도중 하나라도 오류가 나면 원상복구
                for order, user_language in enumerate(user_languages):
                    user_rank, is_created = UserRank.objects.get_or_create(
                        type=f'lang-{language.type}',
                        ranking=order+1
                    )
                    user_rank.github_user_id = user_language.github_user_id
                    user_rank.score = user_language.number
                    user_rank.save(update_fields=['github_user_id', 'score'])

    @staticmethod
    def update_user_ranking():
        """
        total score 로 전체 유저의 순위를 계산하는 함수
        """
        github_users = GithubUser.objects.all()
        for github_user in chunkator(github_users, 1000):
            try:
                github_user.previous_user_rank = github_user.user_rank
                github_user.user_rank = GithubInformationService.update_user_ranking(github_user.total_score)
                github_user.tier = GithubInformationService.get_tier_statistics(github_user.user_rank)
                github_user.save(update_fields=['user_rank', 'previous_user_rank', 'tier'])

            except GitHubUserDoesNotExist:
                continue

            except Exception as e:
                capture_exception(e)


def run():
    """
    새벽 2시에 돌아가는 배치 스크립트
    """
    rank_service = RankService()

    # 랭킹 업데이트 시작
    start_time = timeit.default_timer()  # 시작 시간 체크
    slack_update_ranking_system(status='시작', message='')

    rank_service.run()

    terminate_time = timeit.default_timer()  # 종료 시간 체크
    slack_update_ranking_system(
        status='완료',
        message=f'랭킹 업데이트가 {terminate_time - start_time:.2f}초 걸렸습니다.🎉',
    )
