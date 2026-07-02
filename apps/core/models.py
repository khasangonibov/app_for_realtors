import uuid
from django.db import models


class UUIDModel(models.Model):
    """Абстрактная базовая модель — добавляет UUID вместо обычного
    числового ID. Все модели проекта (кроме User, см. accounts) 
    наследуются от неё.

    abstract = True означает что Django НЕ создаёт отдельную таблицу
    для UUIDModel — поля просто добавляются в дочерние модели.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Частый паттерн — created_at/updated_at.
    Выносим отдельно, чтобы не дублировать в каждой модели.
    """
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        abstract = True