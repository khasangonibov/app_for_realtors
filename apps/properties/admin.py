from django.contrib import admin
from apps.core.admin import SoftDeleteAdminMixin
from .models import Property, PropertyPhoto, PropertyDocument, PropertyFeature, PropertyView


class PropertyPhotoInline(admin.TabularInline):
    """Фото редактируются прямо на странице объекта,
    в виде таблицы — удобно для быстрой загрузки нескольких штук.
    """
    model = PropertyPhoto
    extra = 1  # одна пустая строка для добавления нового фото
    fields = ('image', 'is_cover', 'order')


class PropertyFeatureInline(admin.TabularInline):
    """Доп. характеристики — тоже инлайн, чтобы не уходить
    на отдельную страницу ради пары полей ключ-значение.
    """
    model = PropertyFeature
    extra = 1
    fields = ('key', 'value')


class PropertyDocumentInline(admin.TabularInline):
    model = PropertyDocument
    extra = 0  # документы добавляют реже — не нужна лишняя пустая строка
    fields = ('doc_type', 'name', 'file')


@admin.register(Property)
class PropertyAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        'title', 'agency', 'agent', 'deal_type',
        'property_type', 'price', 'city', 'status',
    )
    list_filter = ('status', 'deal_type', 'property_type', 'city', 'agency')
    search_fields = ('title', 'description', 'street', 'city')
    readonly_fields = ('public_token', 'created_at', 'updated_at')

    inlines = [PropertyPhotoInline, PropertyFeatureInline, PropertyDocumentInline]

    fieldsets = (
        ('Основное', {
            'fields': ('agency', 'agent', 'deal_type', 'property_type', 'status', 'title', 'description')
        }),
        ('Цена', {
            'fields': ('price', 'price_currency', 'commission_percent', 'commission_fixed')
        }),
        ('Площади и комнаты', {
            'fields': ('area_total', 'area_living', 'area_kitchen', 'rooms_count', 'floor', 'floors_total')
        }),
        ('Адрес', {
            'fields': ('city', 'district', 'street', 'building', 'apartment', 'latitude', 'longitude')
        }),
        ('Публикация', {
            'fields': ('is_published', 'is_exclusive', 'public_token')
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(PropertyView)
class PropertyViewAdmin(admin.ModelAdmin):
    """Просмотры — отдельный раздел, так как записей может быть много
    и редактировать их не нужно, только смотреть статистику.
    """
    list_display = ('property', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at',)
    readonly_fields = ('property', 'ip_address', 'user_agent', 'viewed_at')

    def has_add_permission(self, request):
        # Просмотры создаются только программно (при заходе на публичную
        # страницу), вручную добавлять их в админке смысла нет
        return False