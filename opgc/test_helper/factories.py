from dataclasses import dataclass
from typing import Optional

from django.db.models import Model


class ModelFactory:
    model: Optional[Model] = None
    default_data: dict = {}

    @classmethod
    def create(cls, **kwargs) -> Model:
        data = {**cls.default_data, **kwargs}
        return cls.model.objects.create(**data)


class DTOFactory:
    dto: Optional[dataclass] = None
    default_data: dict = {}

    @classmethod
    def create(cls, **kwargs) -> dataclass:
        data = {**cls.default_data, **kwargs}
        return cls.dto(**data)
