"""
Публичные views приложения properties.
Доступны без авторизации — по прямой ссылке с токеном.
"""

from django.shortcuts import render, get_object_or_404
from django.http import Http404

from apps.properties.models import Property


def property_detail(request, agency_slug, pk, token):
    """Публичная карточка объекта недвижимости.

    URL: /object/{agency_slug}/{id}/{token}/

    Безопасность: объект ищем одновременно по pk, agency.slug
    и public_token — все три должны совпасть. Это исключает
    перебор ID (IDOR-атаку) — без правильного token страницу
    не открыть, даже зная ID объекта.
    """
    property_obj = get_object_or_404(
        Property,
        pk=pk,
        public_token=token,
        agency__slug=agency_slug,
    )

    # Если объект не опубликован — отдаём 404, а не "объект скрыт",
    # чтобы не давать сигнал о существовании объекта посторонним
    if not property_obj.is_published:
        raise Http404

    # Фиксируем просмотр — для статистики риелтора.
    # Импортируем здесь, а не в начале файла, чтобы избежать
    # потенциальных циклических импортов между views и models
    _track_view(request, property_obj)

    return render(request, 'properties/public_detail.html', {
        'property': property_obj,
        'photos': property_obj.photos.all(),
        'features': property_obj.features.all(),
    })


def _track_view(request, property_obj):
    """Записывает просмотр объекта для статистики.
    Вынесена в отдельную функцию для читаемости основной view.
    """
    from apps.properties.models import PropertyView

    ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

    PropertyView.objects.create(
        property=property_obj,
        ip_address=ip_address,
        user_agent=user_agent,
    )