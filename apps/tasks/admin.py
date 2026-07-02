from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'task_type', 'priority',
        'agent', 'due_date', 'is_done',
    )
    list_filter = ('is_done', 'priority', 'task_type', 'agency')
    search_fields = ('title', 'description')