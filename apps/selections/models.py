import uuid
from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel
from apps.accounts.models import Agency, User
from apps.contacts.models import Contact
from apps.properties.models import Property


class Selection(UUIDModel, TimeStampedModel):
    """Подборка объектов для конкретного клиента.
    Риелтор создаёт подборку, добавляет объекты и отправляет
    клиенту публичную ссылку. Клиент видит объекты и может
    оставить реакцию на каждый — без авторизации.
    """
    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        related_name='selections',
        verbose_name='Агентство',
    )
    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='selections',
        verbose_name='Риелтор',
        null=True,
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        related_name='selections',
        verbose_name='Клиент',
        null=True, blank=True,
    )
    title = models.CharField('Название', max_length=255)

    # UUID-токен для публичной ссылки — как у объектов
    public_token = models.UUIDField(
        'Токен публичной ссылки',
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    class Meta:
        verbose_name = 'Подборка'
        verbose_name_plural = 'Подборки'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_public_url(self):
        from django.urls import reverse
        return reverse('selection_public:detail', kwargs={
            'token': self.public_token,
        })


class SelectionItem(UUIDModel):
    """Один объект в подборке.
    Хранит комментарий риелтора и реакцию клиента.
    """

    class ClientStatus(models.TextChoices):
        NEW = 'new', 'Не просмотрен'
        LIKED = 'liked', 'Нравится'
        REJECTED = 'rejected', 'Не нравится'
        MAYBE = 'maybe', 'Возможно'

    selection = models.ForeignKey(
        Selection,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Подборка',
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='selection_items',
        verbose_name='Объект',
    )
    agent_comment = models.TextField('Комментарий риелтора', blank=True)
    client_status = models.CharField(
        'Реакция клиента',
        max_length=20,
        choices=ClientStatus.choices,
        default=ClientStatus.NEW,
    )
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Объект в подборке'
        verbose_name_plural = 'Объекты в подборке'
        ordering = ['order']
        # Один объект не может быть добавлен в одну подборку дважды
        unique_together = [['selection', 'property']]

    def __str__(self):
        return f'{self.property} в {self.selection}'