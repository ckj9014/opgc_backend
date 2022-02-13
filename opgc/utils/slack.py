from django.conf import settings
from slackweb import slackweb

from apps.githubs.models import GithubUser


def slack_notify_new_user(user: GithubUser, join_type: str = 'Dirty Boyz'):
    channel = settings.SLACK_CHANNEL_JOINED_USER
    server = 'PROD' if settings.IS_PROD else 'LOCAL'
    attachments = [
        {
            "color": "#36a64f",
            "title": f"유저 등록({join_type})",
            "pretext": f"[{server}] 새로운 유저가 등록되었습니다.🎉",
            "fields": [
                {
                    "title": "아이디",
                    "value": user.username,
                    "short": True
                },
                {
                    "title": "설명",
                    "value": user.bio,
                    "short": True
                },
                {
                    "title": "회사",
                    "value": user.company,
                    "short": True
                }
            ],
            "thumb_url": user.avatar_url
        }
    ]

    if channel:
        slack = slackweb.Slack(url=channel)
        slack.notify(attachments=attachments)


def slack_notify_update_user_queue(username: str):
    """
        Queue 등록 알림
    """
    channel = settings.SLACK_CHANNEL_CRONTAB
    server = 'PROD' if settings.IS_PROD else 'LOCAL'
    attachments = [
        {
            "color": "#ff0000",
            "title": 'RATE LIMIT 제한으로 update 실패',
            "pretext": f'[{server}] {username}이 Queue(DB)에 등록되었습니다.',
        }
    ]

    if channel:
        slack = slackweb.Slack(url=channel)
        slack.notify(attachments=attachments)


def slack_notify_update_fail(message: str):
    channel = settings.SLACK_CHANNEL_CRONTAB
    server = 'PROD' if settings.IS_PROD else 'LOCAL'
    attachments = [
        {
            "color": "#ff0000",
            "title": '업데이트 실패',
            "pretext": f'[{server}] {message}',
        }
    ]

    if channel:
        slack = slackweb.Slack(url=channel)
        slack.notify(attachments=attachments)


def slack_update_github_user(status: str, message: str, update_user=None):
    channel = settings.SLACK_CHANNEL_CRONTAB
    server = 'PROD' if settings.IS_PROD else 'LOCAL'
    fields = []

    if update_user:
        fields.append({
            "title": "총 업데이트 유저",
            "value": f'{update_user} 명',
            "short": True
        })

    attachments = [
        {
            "color": "#36a64f",
            "title": f'💡 예약된 깃헙 유저 정보 업데이트 {status}',
            "fields": fields,
        }
    ]

    if message:
        attachments[0]['pretext'] = f'[{server}] {message}'

    if channel:
        slack = slackweb.Slack(url=channel)
        slack.notify(attachments=attachments)


def slack_update_ranking_system(status: str, message: str):
    channel = settings.SLACK_CHANNEL_CRONTAB
    server = 'PROD' if settings.IS_PROD else 'LOCAL'
    fields = []

    attachments = [
        {
            "color": "#36a64f",
            "title": f'🏆 랭킹 시스템 업데이트 {status}',
            "fields": fields,
        }
    ]

    if message:
        attachments[0]['pretext'] = f'[{server}] {message}'

    if channel:
        slack = slackweb.Slack(url=channel)
        slack.notify(attachments=attachments)


def slack_update_1day_1commit(status: str, message: str):
    channel = settings.SLACK_CHANNEL_CRONTAB
    server = 'PROD' if settings.IS_PROD else 'LOCAL'
    fields = []

    attachments = [
        {
            "color": "#36a64f",
            "title": f'👨‍💻 1일 1커밋 업데이트 {status}',
            "fields": fields,
        }
    ]

    if message:
        attachments[0]['pretext'] = f'[{server}] {message}'

    if channel:
        slack = slackweb.Slack(url=channel)
        slack.notify(attachments=attachments)


def slack_update_older_week_user(status: str, message: str, update_user=None):
    channel = settings.SLACK_CHANNEL_CRONTAB
    server = 'PROD' if settings.IS_PROD else 'LOCAL'
    fields = []

    if update_user:
        fields.append({
            "title": "총 업데이트 유저",
            "value": f'{update_user} 명',
            "short": True
        })

    attachments = [
        {
            "color": "#36a64f",
            "title": f'🥳 업데이트 된지 7일이 지난 유저 업데이트 {status}',
            "fields": fields,
        }
    ]

    if message:
        attachments[0]['pretext'] = f'[{server}] {message}'

    if channel:
        slack = slackweb.Slack(url=channel)
        slack.notify(attachments=attachments)


def slack_update_basic_info(status: str, message: str, update_user=None):
    channel = settings.SLACK_CHANNEL_CRONTAB
    server = 'PROD' if settings.IS_PROD else 'LOCAL'
    fields = []

    if update_user:
        fields.append({
            "title": "총 업데이트 유저",
            "value": f'{update_user} 명',
            "short": True
        })

    attachments = [
        {
            "color": "#36a64f",
            "title": f'🤩 유저 기본 정보 업데이트 {status}',
            "fields": fields,
        }
    ]

    if message:
        attachments[0]['pretext'] = f'[{server}] {message}'

    if channel:
        slack = slackweb.Slack(url=channel)
        slack.notify(attachments=attachments)
