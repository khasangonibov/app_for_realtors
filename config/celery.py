"""
Настройка Celery для асинхронных задач.

Запуск воркера в dev:
  celery -A config worker -l info

Запуск планировщика (периодические задачи):
  celery -A config beat -l info
"""

import os
from celery import Celery

# Django settings используем как источник конфига для Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('realestate_crm')

# Читаем настройки из django settings, ищем ключи с префиксом CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем tasks.py во всех приложениях из INSTALLED_APPS
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Тестовая задача для проверки что Celery работает."""
    print(f'Request: {self.request!r}')