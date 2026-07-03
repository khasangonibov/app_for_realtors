"""
Главный URL-файл проекта.

Структура URL:
  /                    — публичные страницы (карточки объектов, подборки)
  /crm/                — закрытый CRM-интерфейс для риелторов
  /api/v1/             — REST API (для мобильного клиента и интеграций)
  /admin/              — стандартная Django-админка
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ── Django Admin ──────────────────────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ── Публичные страницы (без авторизации) ──────────────────────────────────
    # Карточка объекта: /object/{agency_slug}/{property_id}/{token}/
    # Подборка для клиента: /selection/{token}/
    path('', include('apps.properties.urls.public', namespace='public')),
    path('', include('apps.selections.urls.public', namespace='selection_public')),

    # ── CRM-интерфейс (требует авторизации) ───────────────────────────────────
    path('crm/', include([
        path('', include('apps.accounts.urls', namespace='accounts')),
        path('', include('apps.properties.urls.crm', namespace='properties')),
        path('', include('apps.contacts.urls', namespace='contacts')),
        path('', include('apps.deals.urls', namespace='deals')),
        path('', include('apps.selections.urls.crm', namespace='selections')),
        path('', include('apps.tasks.urls', namespace='tasks')),
        path('', include('apps.analytics.urls', namespace='analytics')),
    ])),

    # ── REST API ───────────────────────────────────────────────────────────────
    # path('api/v1/', include([
    #     path('', include('apps.accounts.api_urls')),
    #     path('', include('apps.properties.api_urls')),
    #     path('', include('apps.contacts.api_urls')),
    #     path('', include('apps.deals.api_urls')),
    #     path('', include('apps.selections.api_urls')),
    # ])),
]

# ── В разработке отдаём медиафайлы через Django ───────────────────────────────
# На production этим занимается nginx или S3
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # debug-toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns