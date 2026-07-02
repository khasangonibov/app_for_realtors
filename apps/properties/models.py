import uuid

from django.db import models
from django.urls import reverse

from apps.core.models import UUIDModel, TimeStampedModel
from apps.accounts.models import Agency, User


class Property(UUIDModel, TimeStampedModel):
    """Объект недвижимости — главная модель приложения.
    Соответствует карточке вроде той, что на crm.topnlab.ru.
    """

    class DealType(models.TextChoices):
        SALE = 'sale', 'Продажа'
        RENT = 'rent', 'Аренда'

    class PropertyType(models.TextChoices):
        APARTMENT = 'apartment', 'Квартира'
        HOUSE = 'house', 'Дом'
        COMMERCIAL = 'commercial', 'Коммерческая недвижимость'
        LAND = 'land', 'Земельный участок'
        GARAGE = 'garage', 'Гараж'
        ROOM = 'room', 'Комната'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Активный'
        RESERVED = 'reserved', 'Забронирован'
        SOLD = 'sold', 'Продан/сдан'
        ARCHIVED = 'archived', 'В архиве'
        DRAFT = 'draft', 'Черновик'

    # ── Связи ──────────────────────────────────────────────────────────────
    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        related_name='properties',
        verbose_name='Агентство',
    )
    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='properties',
        verbose_name='Ответственный риелтор',
        null=True,
        blank=True,
    )

    # ── Тип сделки и объекта ──────────────────────────────────────────────
    deal_type = models.CharField(
        'Тип сделки', max_length=10,
        choices=DealType.choices, default=DealType.SALE,
    )
    property_type = models.CharField(
        'Тип объекта', max_length=20,
        choices=PropertyType.choices, default=PropertyType.APARTMENT,
    )

    # ── Основное описание ────────────────────────────────────────────────
    title = models.CharField('Заголовок', max_length=255, blank=True)
    description = models.TextField('Описание', blank=True)

    # ── Цена ──────────────────────────────────────────────────────────────
    price = models.DecimalField('Цена', max_digits=14, decimal_places=2)
    price_currency = models.CharField('Валюта', max_length=3, default='RUB', blank=True)

    # ── Площади ───────────────────────────────────────────────────────────
    area_total = models.DecimalField(
        'Общая площадь, м²', max_digits=8, decimal_places=2,
        null=True, blank=True,
    )
    area_living = models.DecimalField(
        'Жилая площадь, м²', max_digits=8, decimal_places=2,
        null=True, blank=True,
    )
    area_kitchen = models.DecimalField(
        'Площадь кухни, м²', max_digits=8, decimal_places=2,
        null=True, blank=True,
    )

    # ── Этажность ─────────────────────────────────────────────────────────
    floor = models.PositiveSmallIntegerField('Этаж', null=True, blank=True)
    floors_total = models.PositiveSmallIntegerField(
        'Этажей в доме', null=True, blank=True,
    )
    rooms_count = models.PositiveSmallIntegerField(
        'Количество комнат', null=True, blank=True,
    )

    # ── Адрес ─────────────────────────────────────────────────────────────
    city = models.CharField('Город', max_length=100)
    district = models.CharField('Район', max_length=100, blank=True)
    street = models.CharField('Улица', max_length=255, blank=True)
    building = models.CharField('Дом', max_length=20, blank=True)
    apartment = models.CharField('Квартира/офис', max_length=20, blank=True)

    # ── Координаты для карты ─────────────────────────────────────────────
    latitude = models.DecimalField(
        'Широта', max_digits=10, decimal_places=7,
        null=True, blank=True,
    )
    longitude = models.DecimalField(
        'Долгота', max_digits=10, decimal_places=7,
        null=True, blank=True,
    )

    # ── Статус и публикация ──────────────────────────────────────────────
    status = models.CharField(
        'Статус', max_length=20,
        choices=Status.choices, default=Status.DRAFT,
    )
    is_exclusive = models.BooleanField('Эксклюзивный объект', default=False)
    is_published = models.BooleanField('Опубликован публично', default=False)

    # UUID-токен для публичной ссылки — отдельный от id объекта,
    # чтобы можно было «обнулить» ссылку (выдать новую) не трогая сам объект
    public_token = models.UUIDField(
        'Токен публичной ссылки', default=uuid.uuid4,
        editable=False, unique=True,
    )

    # ── Комиссия ──────────────────────────────────────────────────────────
    commission_percent = models.DecimalField(
        'Комиссия, %', max_digits=5, decimal_places=2,
        null=True, blank=True,
    )
    commission_fixed = models.DecimalField(
        'Комиссия фикс., руб', max_digits=12, decimal_places=2,
        null=True, blank=True,
    )

    class Meta:
        verbose_name = 'Объект недвижимости'
        verbose_name_plural = 'Объекты недвижимости'
        ordering = ['-created_at']  # новые объекты сверху списка
        indexes = [
            models.Index(fields=['agency', 'status']),
            models.Index(fields=['city', 'deal_type', 'property_type']),
        ]

    def __str__(self):
        return self.title or f'{self.get_property_type_display()} в {self.city}'

    @property
    def price_per_sqm(self):
        """Цена за квадратный метр — вычисляется на лету,
        не хранится в БД, чтобы не было рассинхрона с price/area_total.
        """
        if self.area_total and self.area_total > 0:
            return round(self.price / self.area_total, 2)
        return None

    @property
    def cover_photo(self):
        """Главное фото объекта — для превью в списках и OG-тегов."""
        return self.photos.filter(is_cover=True).first() or self.photos.first()

    def get_public_url(self):
        """Ссылка на публичную карточку объекта."""
        return reverse('public:property_detail', kwargs={
            'agency_slug': self.agency.slug,
            'pk': self.pk,
            'token': self.public_token,
        })

class PropertyPhoto(UUIDModel):
    """Фотографии объекта. Одна модель, поле is_cover отмечает
    главное фото для превью в списках и OG-тегах.
    """
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Объект',
    )
    image = models.ImageField('Фото', upload_to='properties/photos/%Y/%m/')
    is_cover = models.BooleanField('Обложка', default=False)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Фото объекта'
        verbose_name_plural = 'Фото объектов'
        ordering = ['order', 'id']  # сортировка для слайдера

    def __str__(self):
        return f'Фото {self.property} (#{self.order})'

    def save(self, *args, **kwargs):
        """Если это фото отмечено как обложка — снимаем флаг
        is_cover со всех остальных фото этого объекта.
        Гарантирует что обложка всегда одна.
        """
        if self.is_cover:
            PropertyPhoto.objects.filter(
                property=self.property, is_cover=True
            ).exclude(pk=self.pk).update(is_cover=False)
        super().save(*args, **kwargs)


class PropertyDocument(UUIDModel, TimeStampedModel):
    """Документы по объекту — договоры, выписки, планы и т.д.
    Хранятся отдельно от фото, так как логически другой тип файла
    и доступ к ним обычно более ограничен (видят не все).
    """

    class DocType(models.TextChoices):
        CONTRACT = 'contract', 'Договор'
        PASSPORT = 'passport', 'Документ собственности'
        PLAN = 'plan', 'План/чертёж'
        OTHER = 'other', 'Другое'

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Объект',
    )
    file = models.FileField('Файл', upload_to='properties/documents/%Y/%m/')
    doc_type = models.CharField(
        'Тип документа', max_length=20,
        choices=DocType.choices, default=DocType.OTHER,
    )
    name = models.CharField('Название', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Документ объекта'
        verbose_name_plural = 'Документы объектов'

    def __str__(self):
        return self.name or f'Документ {self.property}'


class PropertyFeature(UUIDModel):
    """Дополнительные характеристики объекта в формате ключ-значение.
    Например: "Лифт" → "Да", "Парковка" → "Подземная", "Балкон" → "2".

    Такой подход (вместо фиксированных полей в Property) даёт гибкость —
    разные типы объектов имеют разные наборы характеристик, и не нужно
    добавлять миграцию каждый раз когда требуется новый параметр.
    """
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='features',
        verbose_name='Объект',
    )
    key = models.CharField('Характеристика', max_length=100)
    value = models.CharField('Значение', max_length=255)

    class Meta:
        verbose_name = 'Характеристика объекта'
        verbose_name_plural = 'Характеристики объектов'

    def __str__(self):
        return f'{self.key}: {self.value}'


class PropertyView(models.Model):
    """Статистика просмотров публичной карточки объекта.
    Не наследуем UUIDModel — для логов просмотров обычный
    автоинкрементный ID достаточен и эффективнее по месту в БД,
    так как записей может быть очень много.
    """
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name='Объект',
    )
    ip_address = models.GenericIPAddressField('IP адрес')
    user_agent = models.CharField('User-Agent', max_length=500, blank=True)
    viewed_at = models.DateTimeField('Время просмотра', auto_now_add=True)

    class Meta:
        verbose_name = 'Просмотр объекта'
        verbose_name_plural = 'Просмотры объектов'
        indexes = [
            models.Index(fields=['property', 'viewed_at']),
        ]