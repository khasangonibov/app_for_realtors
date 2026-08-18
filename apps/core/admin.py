"""
Переиспользуемые компоненты для Django Admin.
"""

from django.contrib import admin
from django.utils.html import format_html


class SoftDeleteAdminMixin:
    """Подмешивается к ModelAdmin моделей с SoftDeleteModel.
    Показывает статус мягкого удаления в списке, добавляет фильтр
    по дате удаления — чтобы администратор мог найти старые
    soft-deleted записи и удалить их физически через стандартное
    действие Django Admin "Удалить выбранные объекты".
    """

    def get_list_display(self, request):
        base = list(super().get_list_display(request))
        if 'deletion_status' not in base:
            base.append('deletion_status')
        return base

    def get_list_filter(self, request):
        base = list(super().get_list_filter(request))
        if 'is_deleted' not in base:
            base.append('is_deleted')
        if 'deleted_at' not in base:
            base.append('deleted_at')
        return base

    def deletion_status(self, obj):
        if obj.is_deleted:
            date_str = obj.deleted_at.strftime('%d.%m.%Y %H:%M') if obj.deleted_at else '—'
            return format_html(
                '<span style="color: white; background: #dc3545; '
                'padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">'
                'Удалено {}</span>',
                date_str,
            )
        return format_html(
            '<span style="color: white; background: #198754; '
            'padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">Активно</span>'
        )
    deletion_status.short_description = 'Статус'