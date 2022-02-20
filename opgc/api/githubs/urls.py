from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.githubs.views import GithubUserViewSet, OrganizationViewSet, RepositoryViewSet, LanguageViewSet, \
    TierRankViewSet

app_name = 'githubs'

router = DefaultRouter()
router.register(r'', GithubUserViewSet, basename='notice')

organization_list = OrganizationViewSet.as_view({
    'get': 'list',
})

repository_list = RepositoryViewSet.as_view({
    'get': 'list',
})

language_list = LanguageViewSet.as_view({
    'get': 'list',
})

tier_list = TierRankViewSet.as_view({
    'get': 'list',
})

urlpatterns = [
    path(r'users/', include(router.urls)),
    path(r'users/<int:user_pk>/organizations/', organization_list, name='organization_list'),
    path(r'users/<int:user_pk>/repositories/', repository_list, name='repository_list'),
    path(r'languages/', language_list, name='language_list'),
    path(r'tier/', tier_list, name='tier_list'),
]
