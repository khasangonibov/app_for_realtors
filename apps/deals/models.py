from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel, SoftDeleteModel
from apps.accounts.models import Agency, User
from apps.properties.models import Property
from apps.contacts.models import Contact


class Deal(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """Сделка — связывает объект, продавца, покупателя и риелторов.
    Проходит через стадии от переговоров до закрытия.
    """

    class Stage(models.TextChoices):
        NEGOTIATION = 'negotiation', 'Переговоры'
        DEPOSIT = 'deposit', 'Задаток'
        DOCUMENTS = 'documents', 'Документы'
        REGISTRATION = 'registration', 'Регистрация'
        CLOSED = 'closed', 'Закрыта'
        CANCELLED = 'cancelled', 'Отменена'

    # ── Связи ──────────────────────────────────────────────────────────────
    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        related_name='deals',
        verbose_name='Агентство',
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        related_name='deals',
        verbose_name='Объект',
        null=True, blank=True,
    )
    seller_contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        related_name='deals_as_seller',
        verbose_name='Продавец',
        null=True, blank=True,
    )
    buyer_contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        related_name='deals_as_buyer',
        verbose_name='Покупатель',
        null=True, blank=True,
    )
    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='deals',
        verbose_name='Ответственный риелтор',
        null=True, blank=True,
    )

    # ── Стадия и финансы ──────────────────────────────────────────────────
    stage = models.CharField(
        'Стадия', max_length=20,
        choices=Stage.choices,
        default=Stage.NEGOTIATION,
    )
    price_agreed = models.DecimalField(
        'Согласованная цена, ₽',
        max_digits=14, decimal_places=2,
        null=True, blank=True,
    )
    commission_total = models.DecimalField(
        'Комиссия итого, ₽',
        max_digits=12, decimal_places=2,
        null=True, blank=True,
    )
    deposit_amount = models.DecimalField(
        'Задаток, ₽',
        max_digits=12, decimal_places=2,
        null=True, blank=True,
    )
    deposit_date = models.DateField('Дата задатка', null=True, blank=True)
    contract_date = models.DateField('Дата договора', null=True, blank=True)
    close_date = models.DateField('Дата закрытия', null=True, blank=True)

    notes = models.TextField('Заметки', blank=True)

    class Meta:
        verbose_name = 'Сделка'
        verbose_name_plural = 'Сделки'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agency', 'stage']),
        ]

    def __str__(self):
        parts = []
        if self.property:
            parts.append(str(self.property))
        if self.buyer_contact:
            parts.append(self.buyer_contact.full_name)
        return ' — '.join(parts) or f'Сделка #{self.pk}'