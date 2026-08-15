"""
Настройки для локальной разработки.
Включает debug-toolbar и отключает часть ограничений.
"""

from .base import *  # noqa

DEBUG = True

# debug-toolbar показывает SQL запросы, время выполнения, шаблоны
INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE

# debug-toolbar показывается только для этих IP
INTERNAL_IPS = ['127.0.0.1', '::1']

# В разработке разрешаем CORS от фронтенда
CORS_ALLOW_ALL_ORIGINS = True

# Упрощённое логирование в консоль
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',   
            'propagate': False,
        },
    },
}