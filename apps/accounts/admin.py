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
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_role_display', 'agency', 'is_staff', 'is_active')
    list_filter = ('agency', 'is_staff', 'is_active', 'profile__role')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('agency', 'phone', 'avatar')}),
    )

    def get_role_display(self, obj):
        """Показывает роль пользователя в списке — читаемо и сразу видно."""
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return '—'
    get_role_display.short_description = 'Роль'