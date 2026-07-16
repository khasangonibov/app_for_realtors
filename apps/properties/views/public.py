"""
Публичные views приложения properties.
Доступны без авторизации — по прямой ссылке с токеном.
"""

from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.core.paginator import Paginator
from django.db.models import Q

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
    


def catalog(request):
    """Публичный каталог всех опубликованных объектов.
    Доступен без авторизации.
    """
    queryset = Property.objects.filter(
        is_published=True,
        status='active',
    ).select_related(
        'agency', 'agent'
    ).prefetch_related('photos').order_by('-created_at')

    # ── Фильтры ───────────────────────────────────────────────────────────
    deal_type = request.GET.get('deal_type', '')
    property_type = request.GET.get('property_type', '')
    city = request.GET.get('city', '')
    rooms = request.GET.get('rooms', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    search = request.GET.get('search', '').strip()

    if deal_type:
        queryset = queryset.filter(deal_type=deal_type)
    if property_type:
        queryset = queryset.filter(property_type=property_type)
    if city:
        queryset = queryset.filter(city__icontains=city)
    if rooms:
        queryset = queryset.filter(rooms_count=rooms)
    if price_min:
        try:
            queryset = queryset.filter(price__gte=price_min)
        except ValueError:
            pass
    if price_max:
        try:
            queryset = queryset.filter(price__lte=price_max)
        except ValueError:
            pass
    if search:
        queryset = queryset.filter(
            Q(city__icontains=search) |
            Q(street__icontains=search) |
            Q(district__icontains=search) |
            Q(description__icontains=search)
        )

    total_count = queryset.count()

    # Получаем список городов для фильтра
    cities = Property.objects.filter(
        is_published=True, status='active'
    ).values_list('city', flat=True).distinct().order_by('city')

    # Пагинация — 12 объектов на страницу
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'properties/public_catalog.html', {
        'properties': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'cities': cities,
        'deal_types': Property.DealType.choices,
        'property_types': Property.PropertyType.choices,
        # Текущие значения фильтров для сохранения в форме
        'current_deal_type': deal_type,
        'current_property_type': property_type,
        'current_city': city,
        'current_rooms': rooms,
        'current_price_min': price_min,
        'current_price_max': price_max,
        'current_search': search,
    })