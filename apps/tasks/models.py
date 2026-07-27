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
        Agency, on_delete=models.CASCADE,
        related_name='tasks', verbose_name='Агентство',
    )
    agent = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='tasks', verbose_name='Ответственный',
    )
    # Кто назначил задачу — если совпадает с agent, значит поставил себе сам
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        related_name='assigned_tasks', verbose_name='Кто назначил',
        null=True, blank=True,
    )
    contact = models.ForeignKey(
        Contact, on_delete=models.SET_NULL,
        related_name='tasks', verbose_name='Контакт',
        null=True, blank=True,
    )
    related_property = models.ForeignKey(
        Property, on_delete=models.SET_NULL,
        related_name='tasks', verbose_name='Объект',
        null=True, blank=True,
    )

    title = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True)
    task_type = models.CharField(
        'Тип', max_length=20,
        choices=TaskType.choices, default=TaskType.OTHER,
    )
    priority = models.CharField(
        'Приоритет', max_length=10,
        choices=Priority.choices, default=Priority.NORMAL,
    )
    due_date = models.DateTimeField('Срок выполнения')

    # Риелтор отмечает что сделал — но задача ещё не считается закрытой,
    # если требуется подтверждение
    is_done = models.BooleanField('Отмечено выполненным', default=False)
    done_at = models.DateTimeField('Отмечено выполненным в', null=True, blank=True)

    # Подтверждение постановщиком — обязательно только если assigned_by != agent
    is_approved = models.BooleanField('Подтверждено руководителем', default=False)
    approved_at = models.DateTimeField('Подтверждено в', null=True, blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        related_name='approved_tasks', verbose_name='Кто подтвердил',
        null=True, blank=True,
    )

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
        from django.utils import timezone
        return not self.is_done and self.due_date < timezone.now()

    @property
    def needs_approval(self):
        """Задача требует подтверждения, если её назначил кто-то другой
        (не сам риелтор себе), и она ещё не подтверждена."""
        return (
            self.assigned_by_id is not None
            and self.assigned_by_id != self.agent_id
        )

    @property
    def is_fully_completed(self):
        """Задача считается полностью завершённой (попадает в 'выполненные'),
        только когда либо подтверждение не требуется, либо оно получено.
        """
        if not self.needs_approval:
            return self.is_done
        return self.is_done and self.is_approved