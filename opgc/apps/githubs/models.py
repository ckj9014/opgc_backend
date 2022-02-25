from django.db import models

from core.db.models import CustomBaseModel


class GithubUser(CustomBaseModel):
    IRON, BRONZE, SILVER, GOLD, PLATINUM, DIAMOND, MASTER, GRAND_MASTER, CHALLENGER = 0, 5, 10, 15, 20, 25, 30, 33, 35
    GITHUB_RANK_CHOICES = (
        (CHALLENGER, 'Challenger'),
        (GRAND_MASTER, 'GrandMaster'),
        (MASTER, 'Master'),
        (DIAMOND, 'Diamond'),
        (PLATINUM, 'Platinum'),
        (GOLD, 'Gold'),
        (SILVER, 'Silver'),
        (BRONZE, 'Bronze'),
        (IRON, 'Iron')
    )

    NONE, COMPLETED, WAITING, UPDATING, FAIL = 0, 5, 10, 15, 20
    UPDATING_STATUS = (
        (NONE, 'none'),
        (COMPLETED, 'completed'),
        (WAITING, 'waiting'),
        (UPDATING, 'updating'),
        (FAIL, 'fail')
    )

    status = models.SmallIntegerField(choices=UPDATING_STATUS, default=NONE, blank=False, verbose_name='업데이트 상태')
    username = models.CharField(unique=True, max_length=200, null=False, verbose_name='Github ID')
    name = models.CharField(max_length=200, default=None, null=True, blank=True, verbose_name='유저이름')
    email = models.CharField(max_length=200, default=None, null=True, blank=True, verbose_name='이메일')
    location = models.CharField(max_length=200, default=None, null=True, blank=True,
                                verbose_name='국가정보(country)')
    avatar_url = models.CharField(max_length=500, default=None, null=True, blank=True,
                                  verbose_name='깃헙 프로필 URL')
    total_contribution = models.IntegerField(verbose_name='총 컨트리뷰션', default=0)
    total_stargazers_count = models.IntegerField(default=0, verbose_name='총 스타(star)수')
    tier = models.SmallIntegerField(choices=GITHUB_RANK_CHOICES, default=IRON, blank=False, verbose_name='티어')
    user_rank = models.IntegerField(default=None, null=True, verbose_name='현재 랭킹')
    previous_user_rank = models.IntegerField(default=None, null=True, verbose_name='이전 랭킹')
    company = models.CharField(max_length=100, default=None, null=True, blank=True, verbose_name='회사')
    bio = models.CharField(max_length=200, default=None, null=True, blank=True, verbose_name='설명')
    blog = models.CharField(max_length=100, default=None, null=True, blank=True, verbose_name='블로그 주소')
    public_repos = models.IntegerField(default=0, blank=True, verbose_name='공식 레포수')
    followers = models.IntegerField(default=0, blank=True, verbose_name='팔로워')
    following = models.IntegerField(default=0, blank=True, verbose_name='팔로잉')
    continuous_commit_day = models.IntegerField(default=0, verbose_name='1일 1커밋 지속 날짜 카운트')
    total_score = models.IntegerField(default=0, blank=True, verbose_name='종합점수')


class Language(CustomBaseModel):
    type = models.CharField(verbose_name='language_type', unique=True, max_length=100, blank=False)
    github_users = models.ManyToManyField(GithubUser, through='UserLanguage', related_name='language', blank=True)

    def __str__(self):
        return f'{self.type}'


class UserLanguage(CustomBaseModel):
    github_user = models.ForeignKey(GithubUser, db_constraint=False, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, db_constraint=False, on_delete=models.CASCADE)
    number = models.IntegerField(default=0, help_text='number of bytes of code written in that language.')

    class Meta:
        db_table = 'githubs_user_language'
        verbose_name = 'user language'


class Organization(CustomBaseModel):
    name = models.CharField(verbose_name='name', unique=True, max_length=100, blank=False)
    description = models.CharField(verbose_name='description', max_length=500, blank=False, null=True, default=None)
    logo = models.CharField(max_length=500, null=True)
    github_users = models.ManyToManyField(GithubUser, through='UserOrganization', related_name='organization', blank=True)


class UserOrganization(CustomBaseModel):
    github_user = models.ForeignKey(GithubUser, db_constraint=False, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, db_constraint=False, on_delete=models.CASCADE)

    class Meta:
        db_table = 'githubs_user_organization'
        verbose_name = 'user organization'


class Repository(CustomBaseModel):
    github_user = models.ForeignKey(GithubUser, on_delete=models.CASCADE, related_name='repository')
    contribution = models.IntegerField(verbose_name='contribution', default=0)
    stargazers_count = models.IntegerField(default=0)
    name = models.CharField(max_length=100, blank=False)
    full_name = models.CharField(max_length=100, blank=False)
    owner = models.CharField(max_length=100, blank=False)
    organization = models.CharField(max_length=100, blank=False)
    rep_language = models.CharField(max_length=100, blank=False, default='', help_text='대표언어')
    languages = models.CharField(max_length=1000, blank=False, default='',
                                 help_text='레포지토리에서 사용하는 모든 언어(json)')


class Achievements(CustomBaseModel):
    """
    달성 목표 (재미를 위한 컨텐츠)
    """
    summary = models.CharField(verbose_name='summary', max_length=200, blank=False)
