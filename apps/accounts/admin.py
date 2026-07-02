from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Agency, User, UserProfile


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'phone', 'created_at')
    search_fields = ('name', 'city')
    prepopulated_fields = {'slug': ('name',)}  # slug автоматически из name


class UserProfileInline(admin.StackedInline):
    """Показывает профиль (роль) прямо на странице пользователя,
    а не отдельной таблицей.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Расширяем стандартную Django UserAdmin, добавляя наш inline-профиль
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'agency', 'is_staff')
    list_filter = ('agency', 'is_staff', 'is_active')

    # Добавляем agency и phone в форму редактирования
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('agency', 'phone', 'avatar')}),
    )