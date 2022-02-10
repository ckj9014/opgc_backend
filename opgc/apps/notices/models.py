from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models

from core.db.models import CustomBaseModel


class Notice(CustomBaseModel):
    title = models.CharField(max_length=200)
    content = RichTextUploadingField(verbose_name='에디터', blank=True, default='')

    class Meta:
        db_table = 'notice'
        verbose_name = '공지사항'
        verbose_name_plural = '공지사항'

