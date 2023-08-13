from django.conf import settings
from slackweb import slackweb

from apps.githubs.models import GithubUser


class SlackAdapter:
    cron_log_channel = settings.SLACK_CHANNEL_CRONTAB
    user_join_channel = settings.SLACK_CHANNEL_JOINED_USER
    env = 'PROD' if settings.IS_PROD else 'LOCAL'

    @classmethod
    def slack_notify_new_user(cls, user: GithubUser, join_type: str = 'Dirty Boyz'):

        attachments = [
            {
                "color": "#36a64f",
                "title": f"유저 등록({join_type})",
                "pretext": f"[{cls.env}] 새로운 유저가 등록되었습니다.🎉",
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

        cls.send_slack_message(cls.user_join_channel, attachments)

    @classmethod
    def slack_notify_update_user_queue(cls, username: str):
        """
        Queue 등록 알림
        """
        attachments = [
            {
                "color": "#ff0000",
                "title": 'RATE LIMIT 제한으로 update 실패',
                "pretext": f'[{cls.env}] {username}이 Queue(DB)에 등록되었습니다.',
            }
        ]

        cls.send_slack_message(cls.cron_log_channel, attachments)

    @classmethod
    def slack_notify_update_fail(cls, message: str):
        attachments = [{
            "color": "#ff0000",
            "title": '업데이트 실패',
            "pretext": f'[{cls.env}] {message}'
        }]
        cls.send_slack_message(cls.cron_log_channel, attachments)

    @classmethod
    def slack_update_github_user(cls, status: str, message: str, update_user=None):
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
            attachments[0]['pretext'] = f'[{cls.env}] {message}'

        cls.send_slack_message(cls.cron_log_channel, attachments)

    @classmethod
    def slack_update_ranking_system(cls, status: str, message: str):
        fields = []

        attachments = [
            {
                "color": "#36a64f",
                "title": f'🏆 랭킹 시스템 업데이트 {status}',
                "fields": fields,
            }
        ]

        if message:
            attachments[0]['pretext'] = f'[{cls.env}] {message}'

        cls.send_slack_message(cls.cron_log_channel, attachments)

    @classmethod
    def slack_update_1day_1commit(cls, status: str, message: str):
        fields = []

        attachments = [{
            "color": "#36a64f",
            "title": f'👨‍💻 1일 1커밋 업데이트 {status}',
            "fields": fields,
        }]

        if message:
            attachments[0]['pretext'] = f'[{cls.env}] {message}'

        cls.send_slack_message(cls.cron_log_channel, attachments)

    @classmethod
    def slack_update_older_week_user(cls, status: str, message: str, update_user=None):
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
            attachments[0]['pretext'] = f'[{cls.env}] {message}'

        cls.send_slack_message(cls.cron_log_channel, attachments)

    @classmethod
    def slack_update_basic_info(cls, status: str, message: str, update_user=None):
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
            attachments[0]['pretext'] = f'[{cls.env}] {message}'

        cls.send_slack_message(cls.cron_log_channel, attachments)

    @classmethod
    def slack_notice_block(cls, username: str):
        fields = []

        fields.append({
            "title": "유저이름",
            "value": f'{username}',
            "short": True
        })

        attachments = [
            {
                "color": "#36a64f",
                "title": f'유저가 Block 되었습니다',
                "fields": fields,
            }
        ]

        attachments[0]['pretext'] = f'[{cls.env}] 블랙리스트 등록'
        cls.send_slack_message(cls.cron_log_channel, attachments)

    @staticmethod
    def send_slack_message(url: str, attachments: list):
        if not url:
            return
        slack = slackweb.Slack(url=url)
        slack.notify(attachments=attachments)
