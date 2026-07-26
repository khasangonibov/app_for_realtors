from django.contrib import admin
from .models import (
    ManagementContract, Transaction, ManagementDocument,
    ActivityLog, RosreestrVerification,
)


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    fields = ('type', 'category', 'amount', 'date', 'description')


class ManagementDocumentInline(admin.TabularInline):
    model = ManagementDocument
    extra = 0
    fields = ('doc_type', 'name', 'file')


class ActivityLogInline(admin.TabularInline):
    model = ActivityLog
    extra = 0
    fields = ('user', 'action', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ManagementContract)
class ManagementContractAdmin(admin.ModelAdmin):
    list_display = (
        'related_property', 'owner', 'agent',
        'status', 'start_date', 'end_date',
    )
    list_filter = ('status', 'agency')
    search_fields = ('contract_number', 'related_property__city')
    inlines = [TransactionInline, ManagementDocumentInline, ActivityLogInline]

    fieldsets = (
        ('Основное', {
            'fields': (
                'agency', 'related_property', 'owner', 'agent',
                'contract_number', 'status',
            )
        }),
        ('Сроки', {
            'fields': ('start_date', 'end_date')
        }),
        ('Комиссия', {
            'fields': ('commission_type', 'commission_percent', 'commission_fixed')
        }),
        ('Условия', {
            'fields': ('terms',)
        }),
    )


@admin.register(RosreestrVerification)
class RosreestrVerificationAdmin(admin.ModelAdmin):
    list_display = ('contract', 'cadastral_number', 'status', 'checked_at')
    list_filter = ('status',)
    readonly_fields = ('response_data', 'checked_at')