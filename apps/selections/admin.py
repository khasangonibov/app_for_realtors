from django.contrib import admin
from apps.core.admin import SoftDeleteAdminMixin
from .models import Selection, SelectionItem


class SelectionItemInline(admin.TabularInline):
    model = SelectionItem
    extra = 0


@admin.register(Selection)
class SelectionAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'agency', 'agent', 'contact')
    list_filter = ('agency',)
    search_fields = ('title',)
    inlines = [SelectionItemInline]