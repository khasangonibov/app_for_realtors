from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel
from apps.accounts.models import Agency, User


class Contact(UUIDModel, TimeStampedModel):
    """Клиент или лид агентства.
    Контакт всегда привязан к агентству и ответственному риелтору.
    """

    class ContactType(models.TextChoices):
        BUYER = 'buyer', 'Покупатель'
        SELLER = 'seller', 'Продавец'
        TENANT = 'tenant', 'Арендатор'
        LANDLORD = 'landlord', 'Арендодатель'

    class Status(models.TextChoices):
        NEW = 'new', 'Новый'
        IN_PROGRESS = 'in_progress', 'В работе'
        DONE = 'done', 'Завершён'
        REJECTED = 'rejected', 'Отказ'

    class Source(models.TextChoices):
        CALL = 'call', 'Входящий звонок'
        SITE = 'site', 'Сайт'
        REFERRAL = 'referral', 'Рекомендация'
        AVITO = 'avito', 'Авито'
        CIAN = 'cian', 'ЦИАН'
        OTHER = 'other', 'Другое'

    # ── Связи ──────────────────────────────────────────────────────────────
    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name='Агентство',
    )
    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='contacts',
        verbose_name='Ответственный риелтор',
        null=True,
        blank=True,
    )

    # ── Личные данные ─────────────────────────────────────────────────────
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100, blank=True)
    middle_name = models.CharField('Отчество', max_length=100, blank=True)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email', blank=True)

    # ── Тип, статус, источник ─────────────────────────────────────────────
    contact_type = models.CharField(
        'Тип клиента', max_length=20,
        choices=ContactType.choices,
        default=ContactType.BUYER,
    )
    status = models.CharField(
        'Статус', max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    source = models.CharField(
        'Источник', max_length=20,
        choices=Source.choices,
        default=Source.CALL,
    )

    # ── Бюджет (для покупателей/арендаторов) ──────────────────────────────
    budget_min = models.DecimalField(
        'Бюджет от, ₽', max_digits=14, decimal_places=2,
        null=True, blank=True,
    )
    budget_max = models.DecimalField(
        'Бюджет до, ₽', max_digits=14, decimal_places=2,
        null=True, blank=True,
    )

    notes = models.TextField('Заметки', blank=True)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agency', 'status']),
            models.Index(fields=['agency', 'agent']),
        ]

    def get_agent_display_name(self):
            if not self.agent:
                return "—"
            full = self.agent.get_full_name()
            return full if full else self.agent.username
        
    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join(p for p in parts if p) or self.phone


class ContactActivity(UUIDModel):
    """История взаимодействий с клиентом.
    Каждый звонок, встреча, заметка или задача — отдельная запись.
    Это позволяет риелтору видеть всю историю работы с клиентом.
    """

    class ActivityType(models.TextChoices):
        CALL = 'call', 'Звонок'
        MEETING = 'meeting', 'Встреча'
        EMAIL = 'email', 'Email'
        NOTE = 'note', 'Заметка'
        TASK = 'task', 'Задача'

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='Контакт',
    )
    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='activities',
        verbose_name='Риелтор',
        null=True,
    )
    activity_type = models.CharField(
        'Тип', max_length=20,
        choices=ActivityType.choices,
        default=ActivityType.NOTE,
    )
    description = models.TextField('Описание')

    # Для задач — когда запланировано и когда выполнено
    scheduled_at = models.DateTimeField('Запланировано', null=True, blank=True)
    completed_at = models.DateTimeField('Выполнено', null=True, blank=True)
    is_done = models.BooleanField('Выполнено', default=False)

    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Активность'
        verbose_name_plural = 'Активности'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_activity_type_display()} — {self.contact}'