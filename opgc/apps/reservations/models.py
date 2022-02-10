from django.db import models

from core.db.models import CustomBaseModel


class UpdateUserQueue(CustomBaseModel):
    READY, FAIL, PROGRESSING, SUCCESS = 0, 5, 10, 15
    UPDATING_STATUS = (
        (READY, 'ready'),
        (FAIL, 'fail'),
        (PROGRESSING, 'progressing'),
        (SUCCESS, 'success'),
    )

    username = models.CharField(max_length=200, null=False)
    status = models.SmallIntegerField(choices=UPDATING_STATUS, default=READY, blank=False)

    class Meta:
        db_table = 'reservations_update_user_queue'
        verbose_name = 'update_user_queue'
