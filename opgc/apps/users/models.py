from django.db import models

from core.db.models import CustomBaseModel


class User(CustomBaseModel):
    username = models.CharField(unique=True, max_length=200, null=False) # Github ID
    profile_image = models.CharField(max_length=500, null=True) # Github Profile Image URL
