from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel
from apps.accounts.models import Agency, User
from apps.contacts.models import Contact
from apps.properties.models import Property


class Task(UUIDModel, TimeStampedModel):
    """Задача или напоминание для риелтора."""

    class Priority(models.TextChoices):
        LOW = 'low', 'Низкий'
        NORMAL = 'normal', 'Обычный'
        HIGH = 'high', 'Высокий'

    class TaskType(models.TextChoices):
        CALL = 'call', 'Позвонить'
        MEETING = 'meeting', 'Встреча'
        DOCUMENT = 'document', 'Документы'
        OTHER = 'other', 'Другое'

    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Агентство',
    )
    agent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Ответственный',
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        related_name='tasks',
        verbose_name='Контакт',
        null=True, blank=True,
    )
    related_property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        related_name='tasks',
        verbose_name='Объект',
        null=True, blank=True,
    )

    title = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True)
    task_type = models.CharField(
        'Тип', max_length=20,
        choices=TaskType.choices,
        default=TaskType.OTHER,
    )
    priority = models.CharField(
        'Приоритет', max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )
    due_date = models.DateTimeField('Срок выполнения')
    is_done = models.BooleanField('Выполнена', default=False)
    done_at = models.DateTimeField('Выполнена в', null=True, blank=True)

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['is_done', 'due_date']
        indexes = [
            models.Index(fields=['agency', 'agent', 'is_done']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        """Задача просрочена если срок прошёл а она не выполнена."""
        from django.utils import timezone
        return not self.is_done and self.due_date < timezone.now()