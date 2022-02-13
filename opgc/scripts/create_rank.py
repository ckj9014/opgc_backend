from chunkator import chunkator

from apps.githubs.models import Language
from scripts.update_ranking_system import RankService, rank_type_model


def run():
    """
    타입별 랭크 데이터를 생성하는 스크립트
    """
    rank_service = RankService()

    for _type in rank_type_model.keys():
        rank_service.create_new_rank(_type=_type)

    languages = Language.objects.all()
    for language in chunkator(languages, 1000):
        rank_service.create_new_rank(_type=f'lang-{language.type}')
