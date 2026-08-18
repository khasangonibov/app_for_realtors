from django.contrib import admin
from apps.core.admin import SoftDeleteAdminMixin
from .models import Deal


@admin.register(Deal)
class DealAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        'property', 'stage', 'agent',
        'price_agreed', 'close_date', 'created_at',
    )
    list_filter = ('stage', 'agency')
    search_fields = ('property__title', 'buyer_contact__first_name')

    fieldsets = (
        ('Основное', {
            'fields': ('agency', 'agent', 'property', 'stage')
        }),
        ('Участники', {
            'fields': ('seller_contact', 'buyer_contact')
        }),
        ('Финансы', {
            'fields': (
                'price_agreed', 'commission_total',
                'deposit_amount', 'deposit_date',
            )
        }),
        ('Даты', {
            'fields': ('contract_date', 'close_date')
        }),
        ('Заметки', {
            'fields': ('notes',)
        }),
    )