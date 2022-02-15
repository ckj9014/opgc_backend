import pytest
from django.urls import reverse
from rest_framework import status

from apps.users.models import User
from test_helper.request_helper import pytest_request


# @pytest.mark.urls(urls='conf.urls.api')
# @pytest.mark.django_db
# def test_user_list(rf, client, user_context):
#     # TODO: init data 전용 클래스 만들어서 conftest쪽에서 받도록하기
#     # 테스트할 유저 생성
#     User.objects.create(
#         username='jay',
#         profile_image=None
#     )
#
#     url = reverse(viewname="users:user_list")
#     data = {
#         'user_name': 'jay'
#     }
#     response = pytest_request(rf,
#                               method='get',
#                               data=data,
#                               url=url)
#
#     assert response.status_code == status.HTTP_200_OK
