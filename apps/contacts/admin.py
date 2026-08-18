from django.contrib import admin
from apps.core.admin import SoftDeleteAdminMixin
from .models import Contact, ContactActivity


class ContactActivityInline(admin.TabularInline):
    """История взаимодействий прямо на странице контакта."""
    model = ContactActivity
    extra = 0
    fields = ('activity_type', 'description', 'scheduled_at', 'is_done')
    readonly_fields = ('created_at',)


@admin.register(Contact)
class ContactAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        'full_name', 'phone', 'contact_type',
        'status', 'source', 'agent', 'created_at',
    )
    list_filter = ('status', 'contact_type', 'source', 'agency')
    search_fields = ('first_name', 'last_name', 'phone', 'email')
    inlines = [ContactActivityInline]

    fieldsets = (
        ('Личные данные', {
            'fields': (
                'agency', 'agent',
                'last_name', 'first_name', 'middle_name',
                'phone', 'email',
            )
        }),
        ('Статус и источник', {
            'fields': ('contact_type', 'status', 'source')
        }),
        ('Бюджет', {
            'fields': ('budget_min', 'budget_max'),
            'classes': ('collapse',),
        }),
        ('Заметки', {
            'fields': ('notes',)
        }),
    )