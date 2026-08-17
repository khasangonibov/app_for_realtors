from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel, SoftDeleteModel
from apps.accounts.models import Agency, User
from apps.contacts.models import Contact
from apps.properties.models import Property


class ManagementContract(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """Договор доверительного управления объектом.
    Связывает объект, собственника (контакт) и управляющего агента.
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Действующий'
        PAUSED = 'paused', 'Приостановлен'
        TERMINATED = 'terminated', 'Расторгнут'
        DRAFT = 'draft', 'Черновик'

    class CommissionType(models.TextChoices):
        PERCENT = 'percent', 'Процент от дохода'
        FIXED = 'fixed', 'Фиксированная сумма'

    agency = models.ForeignKey(
        Agency, on_delete=models.CASCADE,
        related_name='management_contracts',
        verbose_name='Агентство',
    )
    related_property = models.OneToOneField(
        Property, on_delete=models.CASCADE,
        related_name='management_contract',
        verbose_name='Объект',
    )
    owner = models.ForeignKey(
        Contact, on_delete=models.PROTECT,
        related_name='owned_contracts',
        verbose_name='Собственник',
    )
    agent = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        related_name='managed_contracts',
        verbose_name='Управляющий агент',
        null=True,
    )

    contract_number = models.CharField('Номер договора', max_length=50, blank=True)
    start_date = models.DateField('Дата начала')
    end_date = models.DateField('Дата окончания', null=True, blank=True)
    status = models.CharField(
        'Статус', max_length=20,
        choices=Status.choices, default=Status.DRAFT,
    )

    commission_type = models.CharField(
        'Тип комиссии', max_length=10,
        choices=CommissionType.choices, default=CommissionType.PERCENT,
    )
    commission_percent = models.DecimalField(
        'Комиссия, %', max_digits=5, decimal_places=2,
        null=True, blank=True,
    )
    commission_fixed = models.DecimalField(
        'Комиссия фикс., ₽/мес', max_digits=10, decimal_places=2,
        null=True, blank=True,
    )

    terms = models.TextField('Условия договора', blank=True)

    class Meta:
        verbose_name = 'Договор управления'
        verbose_name_plural = 'Договоры управления'
        ordering = ['-created_at']

    def __str__(self):
        return f'Управление: {self.related_property} ({self.owner.full_name})'

    @property
    def total_income(self):
        return self.transactions.filter(
            type=Transaction.Type.INCOME
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0

    @property
    def total_expense(self):
        return self.transactions.filter(
            type=Transaction.Type.EXPENSE
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0

    @property
    def net_income(self):
        result = self.total_income - self.total_expense
        return result


class Transaction(UUIDModel):
    """Доход или расход по объекту в управлении."""

    class Type(models.TextChoices):
        INCOME = 'income', 'Доход'
        EXPENSE = 'expense', 'Расход'

    class Category(models.TextChoices):
        RENT = 'rent', 'Арендная плата'
        UTILITIES = 'utilities', 'Коммунальные услуги'
        REPAIR = 'repair', 'Ремонт'
        COMMISSION = 'commission', 'Комиссия агентства'
        TAX = 'tax', 'Налоги'
        INSURANCE = 'insurance', 'Страхование'
        OTHER = 'other', 'Другое'

    contract = models.ForeignKey(
        ManagementContract, on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Договор',
    )
    type = models.CharField(
        'Тип', max_length=10,
        choices=Type.choices,
    )
    category = models.CharField(
        'Категория', max_length=20,
        choices=Category.choices, default=Category.OTHER,
    )
    amount = models.DecimalField('Сумма, ₽', max_digits=12, decimal_places=2)
    date = models.DateField('Дата')
    description = models.CharField('Описание', max_length=255, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        related_name='created_transactions',
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-date']

    def __str__(self):
        sign = '+' if self.type == self.Type.INCOME else '-'
        return f'{sign}{self.amount} ₽ — {self.get_category_display()}'


class ManagementDocument(UUIDModel, TimeStampedModel):
    """Документы по объекту в управлении — правоустанавливающие
    и прочие. Доступ ограничен агентом и собственником.
    """

    class DocType(models.TextChoices):
        OWNERSHIP = 'ownership', 'Правоустанавливающий документ'
        EGRN = 'egrn', 'Выписка ЕГРН'
        CONTRACT = 'contract', 'Договор управления (скан)'
        INSURANCE = 'insurance', 'Страховой полис'
        INVENTORY = 'inventory', 'Опись имущества'
        OTHER = 'other', 'Другое'

    contract = models.ForeignKey(
        ManagementContract, on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Договор',
    )
    doc_type = models.CharField(
        'Тип документа', max_length=20,
        choices=DocType.choices, default=DocType.OTHER,
    )
    name = models.CharField('Название', max_length=255)
    file = models.FileField('Файл', upload_to='management/documents/%Y/%m/')
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='uploaded_management_documents',
    )

    class Meta:
        verbose_name = 'Документ управления'
        verbose_name_plural = 'Документы управления'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ActivityLog(models.Model):
    """Журнал действий по договору управления —
    для прозрачности перед собственником."""

    contract = models.ForeignKey(
        ManagementContract, on_delete=models.CASCADE,
        related_name='activity_log',
        verbose_name='Договор',
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        verbose_name='Пользователь',
    )
    action = models.CharField('Действие', max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Запись журнала'
        verbose_name_plural = 'Журнал действий'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} — {self.created_at:%d.%m.%Y %H:%M}'


class RosreestrVerification(UUIDModel):
    """Заглушка для будущей интеграции с API Росреестра (ФГИС ЕГРН).
    Хранит статус проверки прав собственности по кадастровому номеру.
    Реальный запрос к API будет добавлен отдельно —
    требует аккредитации и платного доступа к ФГИС ЕГРН.
    """

    class Status(models.TextChoices):
        NOT_CHECKED = 'not_checked', 'Не проверено'
        PENDING = 'pending', 'Запрос отправлен'
        VERIFIED = 'verified', 'Подтверждено'
        MISMATCH = 'mismatch', 'Расхождение данных'
        ERROR = 'error', 'Ошибка проверки'

    contract = models.OneToOneField(
        ManagementContract, on_delete=models.CASCADE,
        related_name='rosreestr_check',
        verbose_name='Договор',
    )
    cadastral_number = models.CharField(
        'Кадастровый номер', max_length=50, blank=True,
    )
    status = models.CharField(
        'Статус проверки', max_length=20,
        choices=Status.choices, default=Status.NOT_CHECKED,
    )
    response_data = models.JSONField(
        'Ответ API', null=True, blank=True,
        help_text='Сырой ответ от ФГИС ЕГРН (когда интеграция будет подключена)',
    )
    checked_at = models.DateTimeField('Проверено в', null=True, blank=True)

    class Meta:
        verbose_name = 'Проверка Росреестра'
        verbose_name_plural = 'Проверки Росреестра'

    def __str__(self):
        return f'{self.cadastral_number or "—"}: {self.get_status_display()}'