# from unittest import mock
#
# import pytest
#
#
# @pytest.fixture(scope='session', autouse=True)
# def mock_slack_notify_new_user():
#     with mock.patch('utils.slack.slack_notify_new_user') as patch:
#         yield patch
