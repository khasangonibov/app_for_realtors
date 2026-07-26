from django.db import models
from apps.core.models import TimeStampedModel, UUIDModel
from apps.accounts.models import User, Agency
from apps.contacts.models import Contact


class ChatRoom(UUIDModel):
    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        related_name='chat_rooms',
        verbose_name='Агентство',
    )
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_rooms_as_client',
        verbose_name='Клиент',
    )
    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='chat_rooms_as_agent',
        verbose_name='Риелтор',
        null=True, blank=True,
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        related_name='chat_rooms',
        verbose_name='Контакт',
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        verbose_name = 'Комната чата'
        verbose_name_plural = 'Комнаты чата'
        # Убираем старый unique_together по (agency, client)
        # Теперь уникальность по тройке: агентство + клиент + риелтор
        # agent=None означает чат "без риелтора" (общий)
        unique_together = [['agency', 'client', 'agent']]

    def __str__(self):
        agent_name = self.agent.get_full_name() if self.agent else 'Общий'
        return f'Чат {self.client} — {agent_name}'
    
    
class Message(UUIDModel):
    """Сообщение в чате."""
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Комната',
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Отправитель',
    )
    text = models.TextField('Текст сообщения')
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='replies',
        verbose_name='Ответ на сообщение',
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField('Прочитано', default=False)

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender}: {self.text[:50]}'
    
class InternalChat(UUIDModel, TimeStampedModel):
    """Внутренний чат между сотрудниками агентства.
    Может быть личным (2 участника) или групповым (3+).
    """
    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        related_name='internal_chats',
        verbose_name='Агентство',
    )
    name = models.CharField(
        'Название группы', max_length=255, blank=True,
        help_text='Заполняется только для групповых чатов',
    )
    participants = models.ManyToManyField(
        User,
        related_name='internal_chats',
        verbose_name='Участники',
    )
    is_group = models.BooleanField('Групповой чат', default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_internal_chats',
        verbose_name='Создатель',
        null=True,
    )

    class Meta:
        verbose_name = 'Внутренний чат'
        verbose_name_plural = 'Внутренние чаты'
        ordering = ['-created_at']

    def __str__(self):
        if self.is_group:
            return self.name or 'Групповой чат'
        participants_names = ', '.join(
            p.get_full_name() or p.username
            for p in self.participants.all()[:2]
        )
        return participants_names

    def get_display_name(self, current_user):
        """Название чата для показа конкретному пользователю.
        Для личного чата — имя собеседника, для группового — название группы.
        """
        if self.is_group:
            return self.name or 'Групповой чат'
        other = self.participants.exclude(pk=current_user.pk).first()
        if other:
            return other.get_full_name() or other.username
        return 'Чат'


class InternalMessage(UUIDModel):
    """Сообщение во внутреннем чате."""
    chat = models.ForeignKey(
            InternalChat,
            on_delete=models.CASCADE,
            related_name='messages',
            verbose_name='Чат',
        )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_internal_messages',
        verbose_name='Отправитель',
    )
    text = models.TextField('Текст сообщения')
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='replies',
        verbose_name='Ответ на сообщение',
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Внутреннее сообщение'
        verbose_name_plural = 'Внутренние сообщения'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender}: {self.text[:50]}'


class InternalMessageRead(models.Model):
    """Отметки о прочтении сообщений во внутреннем чате.
    Отдельная модель, потому что у группового чата несколько
    получателей — каждому нужна своя отметка прочтения.
    """
    message = models.ForeignKey(
        InternalMessage,
        on_delete=models.CASCADE,
        related_name='read_by',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='read_internal_messages',
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['message', 'user']]