from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
import urllib.parse as urlparse
from urllib.parse import parse_qs


class BaseCursorPagination(CursorPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000
    ordering = 'id'

    def get_paginated_response(self, data) -> Response:
        return Response({
            'next': self.get_cursor(self.get_next_link()),
            'previous': self.get_cursor(self.get_previous_link()),
            'results': data
        })

    @staticmethod
    def get_cursor(cursor_link: str):
        parsed = urlparse.urlparse(cursor_link)
        cursor = parse_qs(parsed.query).get('cursor')

        if cursor:
            return cursor[0]
        else:
            return None


class IdOrderingPagination(BaseCursorPagination):
    page_size = 10
    max_page_size = 1000
    ordering = 'id'


class DescIdOrderingPagination(BaseCursorPagination):
    page_size = 10
    max_page_size = 1000
    ordering = '-id'


class TierOrderingPagination(BaseCursorPagination):
    page_size = 10
    max_page_size = 1000
    ordering = ('-tier', '-continuous_commit_day')


class ScoreOrderingPagination(BaseCursorPagination):
    page_size = 10
    max_page_size = 1000
    ordering = ('-score',)


class UserRankOrderingPagination(BaseCursorPagination):
    page_size = 10
    max_page_size = 1000
    ordering = ('user_rank',)


class TotalScorePagination(BaseCursorPagination):
    page_size = 10
    max_page_size = 1000
    ordering = ('-total_score',)
