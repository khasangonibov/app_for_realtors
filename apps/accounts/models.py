import uuid
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel


class Agency(UUIDModel, TimeStampedModel):
    """Агентство недвижимости.
    
    Система работает по принципу «один сервер — одно агентство»:
    вторую запись создать нельзя, save() блокирует это на уровне модели.
    """
    name = models.CharField('Название', max_length=255)
    slug = models.SlugField('Slug', unique=True)
    logo = models.ImageField('Логотип', upload_to='agency/logos/', blank=True)
    city = models.CharField('Город', max_length=100, blank=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    email = models.EmailField('Email', blank=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Агентство'
        verbose_name_plural = 'Агентства'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Разрешает только одну запись Agency в системе.
        Обновление существующей записи (тот же pk) — можно всегда.
        Создание новой при уже существующей — запрещено.
        """
        if not self.pk and Agency.objects.exists():
            raise ValidationError(
                'В системе уже есть агентство. '
                'Эта CRM работает по принципу «один сервер — одно агентство», '
                'создание второй записи запрещено.'
            )
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        """Возвращает единственную запись агентства.
        Используется везде вместо Agency.objects.first(),
        чтобы явно выразить что агентство ровно одно.
        """
        return cls.objects.first()


class User(AbstractUser):
    """Кастомная модель пользователя.
    Наследуем AbstractUser — получаем username, email,
    password, first_name, last_name, is_active и т.д.
    Добавляем только то что нам нужно сверху.

    Примечание: UUID здесь задаём явно (а не через UUIDModel),
    потому что множественное наследование от AbstractUser и UUIDModel
    может вызвать конфликт полей.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    agency = models.ForeignKey(
        Agency, on_delete=models.CASCADE, related_name='users',
        verbose_name='Агентство', null=True, blank=True,
    )
    email = models.EmailField('Email', unique=True, blank=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    avatar = models.ImageField('Аватар', upload_to='users/avatars/', blank=True)

    # Логинимся по email, а не по username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.get_full_name()} ({self.email})'

    @property
    def role(self):
        """Удобное свойство для получения роли."""
        if hasattr(self, 'profile'):
            return self.profile.role
        return None

    @property
    def is_agent(self):
        return self.role == UserProfile.Role.AGENT

    @property
    def is_manager(self):
        return self.role == UserProfile.Role.MANAGER

    @property
    def is_admin(self):
        return self.role == UserProfile.Role.ADMIN

    @property
    def is_client(self):
        return self.role == UserProfile.Role.CLIENT


class UserProfile(UUIDModel):
    """Профиль пользователя — роль и доп. данные.
    Отделяем от User чтобы не раздувать основную модель.
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Администратор'           # полный доступ
        MANAGER = 'manager', 'Руководитель'        # добавление сотрудников, доп. аналитика по сотрудникам, все объекты
        AGENT = 'agent', 'Риелтор'                 # все публичные объекты, объекты находящиеся в доверительном управлении только свои
        CLIENT = 'client', 'Внешний пользователь'  # авторизованный клиент

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(
        'Роль',
        max_length=20,
        choices=Role.choices,
        default=Role.AGENT,
    )
    bio = models.TextField('О себе', blank=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'{self.user} — {self.get_role_display()}'