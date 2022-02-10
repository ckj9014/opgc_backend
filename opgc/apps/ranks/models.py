from django.db import models

from apps.githubs.models import GithubUser
from core.db.models import CustomBaseModel


class UserRank(CustomBaseModel):
    type = models.CharField(max_length=200, null=False)
    ranking = models.SmallIntegerField(default=0, blank=False)
    score = models.IntegerField(default=0, blank=False)
    github_user = models.ForeignKey(GithubUser, db_constraint=False, on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name = 'user_rank'
