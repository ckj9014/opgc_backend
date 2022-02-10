"""
    새벽 2시에 돌아가는 배치 스크립트
"""
import timeit

from chunkator import chunkator
from django.db import transaction

from apps.githubs.models import GithubUser, Language, UserLanguage
from apps.ranks.models import UserRank
from core.github_service import GithubInformationService
from utils.exceptions import GitHubUserDoesNotExist
from utils.slack import slack_update_ranking_system

# todo : 이거 수정하기 (원래 필드 : 모델 이런형태로 하려고 했는데 그렇게 안씀)
rank_type_model = {
    'continuous_commit_day': GithubUser,
    'total_contribution': GithubUser,
    'total_stargazers_count': GithubUser,
    'followers': GithubUser,
    'following': GithubUser
}


class RankService(object):
    # todo: 현재는 데이터가 별로 없어서 order by를 했는데, 더 좋은 아이디어가 있는지 확인 필요!
    #       동점자 처리 어떻게 할지 고민해봐야함!

    @staticmethod
    def create_new_rank(_type: str):
        """
        새로운 type의 rank를 1-10까지 만든다
        """

        if UserRank.objects.filter(type=_type).exists():
            return

        new_ranks = []
        for idx in range(1, 11):
            new_ranks.append(UserRank(type=_type, ranking=idx, score=0, github_user=None))

        UserRank.objects.bulk_create(new_ranks)

    def update_all_rank(self):
        for _type in rank_type_model.keys():
            self.update_rank(_type)

        self.update_language_rank()
        self.update_user_ranking()

    @staticmethod
    def update_rank(_type: str):
        rank = rank_type_model.get(_type)

        if not rank:
            return

        github_user_data = GithubUser.objects.values('id', _type).order_by(f'-{_type}')[:10]

        # 랭킹 업데이트 도중 하나라도 오류가 나면 원상복구
        with transaction.atomic():
            # 최대 10개라 all()로 그냥 가져옴
            # todo: user 가 많아지면 100개로 늘릴예정
            for order, data in enumerate(github_user_data):
                user_rank, is_created = UserRank.objects.get_or_create(type=_type, ranking=order+1)
                user_rank.github_user_id = data.get('id')
                user_rank.score = data.get(_type)
                user_rank.save(update_fields=['github_user_id', 'score'])

    @staticmethod
    def update_language_rank():
        """
        언어별 count 값으로 랭킹
        """

        languages = Language.objects.all()

        for language in chunkator(languages, 1000):
            user_languages = UserLanguage.objects.filter(language_id=language.id).order_by('-number')[:10]

            # 랭킹 업데이트 도중 하나라도 오류가 나면 원상복구
            with transaction.atomic():
                for order, user_language in enumerate(user_languages):
                    user_rank, is_created = UserRank.objects.get_or_create(type=f'lang-{language.type}', ranking=order+1)
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
                github_user.user_rank = GithubInformationService.update_user_ranking(github_user.total_score)
                github_user.tier = GithubInformationService.get_tier_statistics(github_user.user_rank)
                github_user.save(update_fields=['user_rank', 'tier'])

            except GitHubUserDoesNotExist:
                continue


def run():
    rank_service = RankService()

    # 먼저 새로 추가된 language 가 있으면 추가해준다
    for _type in rank_type_model.keys():
        rank_service.create_new_rank(_type=_type)

    languages = Language.objects.all()
    for language in chunkator(languages, 1000):
        rank_service.create_new_rank(_type=f'lang-{language.type}')

    # 랭킹 업데이트 시작
    start_time = timeit.default_timer()  # 시작 시간 체크
    slack_update_ranking_system(status='시작', message='')

    rank_service.update_all_rank()

    terminate_time = timeit.default_timer()  # 종료 시간 체크
    slack_update_ranking_system(
        status='완료',
        message=f'랭킹 업데이트가 {terminate_time - start_time:.2f}초 걸렸습니다.🎉',
    )
