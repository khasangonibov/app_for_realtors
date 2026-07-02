"""
ASGI config — точка входа для асинхронных серверов (uvicorn, daphne).
Нужен для WebSocket, если будут real-time уведомления в будущем.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

application = get_asgi_application()