"""
Публичные URL приложения properties.
Подключаются в config/urls.py без префикса (на верхнем уровне).
"""

from django.urls import path

from apps.properties.views import public as views

app_name = 'public'

urlpatterns = [
    # /object/{agency_slug}/{id}/{token}/
    path(
        'object/<slug:agency_slug>/<uuid:pk>/<uuid:token>/',
        views.property_detail,
        name='property_detail',
    ),
]