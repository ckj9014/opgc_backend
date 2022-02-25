from datetime import timedelta, datetime

from django.http import HttpResponse
from django.template import loader
from django.template.response import TemplateResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, exceptions
from rest_framework.decorators import action
from rest_framework.response import Response

from api.exceptions import NotExistsGithubUser, RateLimitGithubAPI
from api.githubs.serializers import OrganizationSerializer, RepositorySerializer, LanguageSerializer, \
    GithubUserListSerializer, GithubUserSerializer
from api.paginations import IdOrderingPagination, TierOrderingPagination, TotalScorePagination, DescIdOrderingPagination
from api.ranks.serializers import TierSerializer
from apps.githubs.models import GithubUser, Organization, Repository, Language
from utils.exceptions import GitHubUserDoesNotExist, RateLimit
from core.services.github_service import GithubInformationService


class GithubUserViewSet(mixins.UpdateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """
    endpoint : githubs/users/:username
    """

    queryset = GithubUser.objects.prefetch_related('organization', 'repository', 'language').all()
    serializer_class = GithubUserListSerializer
    pagination_class = TotalScorePagination
    lookup_url_kwarg = 'username'
    lookup_field = 'username'

    def get_queryset(self):
        data = self.request.GET
        queryset = self.queryset

        if data.get('company'):
            queryset = queryset.filter(company__icontains=data.get('company'))

        if data.get('username'):
            queryset = queryset.filter(username__icontains=data.get('username'))

        if data.get('tier'):
            queryset = queryset.filter(tier=data.get('tier'))

        return queryset

    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = GithubUserSerializer
        username = self.kwargs.get(self.lookup_url_kwarg)
        github_user = self.get_queryset().filter(username=username).first()

        if not github_user:
            try:
                github_information_service = GithubInformationService(username)
                github_user = github_information_service.update()

            except GitHubUserDoesNotExist:
                raise NotExistsGithubUser()

            except RateLimit:
                raise RateLimitGithubAPI()

        serializer = self.serializer_class(github_user)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        self.serializer_class = GithubUserSerializer
        username = self.kwargs.get(self.lookup_url_kwarg)

        try:
            github_user = GithubUser.objects.filter(username=username).get()

            if self.can_update(updated_date=github_user.updated) is False:
                response_data = self.serializer_class(github_user).data
                return Response(response_data)

            github_information_service = GithubInformationService(username)
            user = github_information_service.update()
            response_data = self.serializer_class(user).data

        except GithubUser.DoesNotExist:
            raise exceptions.NotFound

        except RateLimit:
            raise RateLimitGithubAPI()

        return Response(response_data)

    @action(methods=['GET'], detail=True, url_path='tag', url_name='tag')
    def tag(self, request, *args, **kwargs):
        """
        OPGC 프로필 svg tag 를 리턴합니다.
        """
        # todo: TemplateResponse header 를 django 3.2 부터 사용가능
        #       django version up 이후 사용예정
        # context = {'github_user': self.get_object()}
        # headers = {'Cache-Control': ' max-age=43200'}
        # return TemplateResponse(
        #     # headers=headers,
        #     request=request,
        #     context=context,
        #     content_type='image/svg+xml',
        #     template=loader.get_template('tag/profile.html')
        # )
        # todo: 함수 정리하기
        github_user = self.get_object()
        border = request.GET.get('border', 'normal')
        template = loader.get_template('tag/profile.html')
        context = {'github_user': github_user, 'border': border}
        response = HttpResponse(content=template.render(context, request))
        response['Content-Type'] = 'image/svg+xml'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    @staticmethod
    def can_update(updated_date: datetime):
        """업데이트 한지 하루가 지나야지 재업데이트 가능"""
        return updated_date + timedelta(1) <= datetime.now()


class OrganizationViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    """
    endpoint : githubs/users/:user_pk/organizations/
    """

    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    lookup_url_kwarg = 'user_pk'

    def get_queryset(self):
        user_pk = self.kwargs.get(self.lookup_url_kwarg)
        organizations = Organization.objects.filter(org__github_user_id=user_pk)
        return organizations

    def list(self, request, *args, **kwargs):
        organizations = self.get_queryset()
        serializer = self.serializer_class(organizations, many=True)
        return Response(serializer.data)


class RepositoryViewSet(mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """
    endpoint : githubs/:user_pk/repositories/
    """

    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer
    pagination_class = DescIdOrderingPagination
    lookup_url_kwarg = 'user_pk'

    def get_queryset(self):
        user_pk = self.kwargs.get(self.lookup_url_kwarg)
        repositories = Repository.objects.filter(github_user_id=user_pk)
        return repositories


class LanguageViewSet(mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """
    endpoint : githubs/languages/
    """

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    pagination_class = IdOrderingPagination


class TierRankViewSet(mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """
    endpoint : githubs/tier/
    todo: 곧 삭제 예정인 API
    """

    queryset = GithubUser.objects.all()
    serializer_class = TierSerializer
    pagination_class = TierOrderingPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tier']
