from datetime import datetime

from cacheops import invalidate_obj
from django.db import models
from django.db.models import QuerySet
from sentry_sdk import capture_exception


class BaseQueryset(QuerySet):
    def update(self, **kwargs):
        row = super().update(**kwargs)

        try:
            """
            django-cacheops 는 update 쿼리를 invalidate 해주지 않기 때문에
            이렇게 커스텀 하거나 invalidated_update() 를 써줘야 한다
            """
            invalidate_obj(self.get())
        except self.model.DoesNotExist:
            capture_exception(Exception(f'{self.model} : invalidate update fail'))

        return row


class BaseManger(models.Manager):
    def get_queryset(self):
        return BaseQueryset(self.model, using=self.db)


class CustomBaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = BaseManger()

    class Meta:
        abstract = True
        default_manager_name = 'objects'  # 명시적으로 적용

    # todo: 제거해야 함 (auto_now 옵션이 있어서 필요가 없음)
    def save(self, *args, **kwargs):
        """ On save, update timestamps """
        if not self.id:
            self.created = datetime.now()
        self.updated = datetime.now()
        return super().save(*args, **kwargs)
