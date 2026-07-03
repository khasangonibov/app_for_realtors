from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from apps.properties.models import Property, PropertyView
from apps.contacts.models import Contact
from apps.deals.models import Deal
from apps.accounts.models import User


@login_required
def analytics_dashboard(request):
    """Полноценная страница аналитики агентства."""
    agency = request.user.agency
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # ── Объекты по статусам ───────────────────────────────────────────────
    properties_by_status = list(
        Property.objects.filter(agency=agency)
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )

    # ── Объекты по типам ──────────────────────────────────────────────────
    properties_by_type = list(
        Property.objects.filter(agency=agency)
        .values('property_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # ── Воронка контактов ─────────────────────────────────────────────────
    contacts_funnel = list(
        Contact.objects.filter(agency=agency)
        .values('status')
        .annotate(count=Count('id'))
    )

    # ── Сделки по стадиям ─────────────────────────────────────────────────
    deals_by_stage = list(
        Deal.objects.filter(agency=agency)
        .exclude(stage__in=['closed', 'cancelled'])
        .values('stage')
        .annotate(
            count=Count('id'),
            total=Sum('price_agreed'),
        )
    )

    # ── Закрытые сделки за 30 дней ────────────────────────────────────────
    closed_deals = Deal.objects.filter(
        agency=agency,
        stage='closed',
        close_date__gte=thirty_days_ago.date(),
    )
    closed_deals_count = closed_deals.count()
    closed_deals_sum = closed_deals.aggregate(
        total=Sum('price_agreed')
    )['total'] or 0

    # ── Просмотры объектов за 30 дней ─────────────────────────────────────
    views_by_day = list(
        PropertyView.objects.filter(
            property__agency=agency,
            viewed_at__gte=thirty_days_ago,
        )
        .extra(select={'day': "DATE(viewed_at)"})
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    # ── Топ объектов по просмотрам ────────────────────────────────────────
    top_properties = list(
        Property.objects.filter(agency=agency)
        .annotate(views_count=Count('views'))
        .order_by('-views_count')[:5]
    )

    # ── Эффективность риелторов (только для admin/manager) ────────────────
    agents_stats = None
    if not request.user.is_agent:
        agents_stats = list(
            User.objects.filter(agency=agency)
            .annotate(
                properties_count=Count('properties', distinct=True),
                contacts_count=Count('contacts', distinct=True),
                deals_count=Count('deals', distinct=True),
            )
            .filter(
                Q(properties_count__gt=0) |
                Q(contacts_count__gt=0) |
                Q(deals_count__gt=0)
            )
            .order_by('-deals_count')
        )

    # Переводим choices в словари для удобного доступа в шаблоне
    status_labels = dict(Property.Status.choices)
    type_labels = dict(Property.PropertyType.choices)
    contact_status_labels = dict(Contact.Status.choices)
    deal_stage_labels = dict(Deal.Stage.choices)

    return render(request, 'analytics/dashboard.html', {
        'properties_by_status': [
            {'label': status_labels.get(item['status'], item['status']),
             'count': item['count']}
            for item in properties_by_status
        ],
        'properties_by_type': [
            {'label': type_labels.get(item['property_type'], item['property_type']),
             'count': item['count']}
            for item in properties_by_type
        ],
        'contacts_funnel': [
            {'label': contact_status_labels.get(item['status'], item['status']),
             'count': item['count']}
            for item in contacts_funnel
        ],
        'deals_by_stage': [
            {'label': deal_stage_labels.get(item['stage'], item['stage']),
             'count': item['count'],
             'total': item['total'] or 0}
            for item in deals_by_stage
        ],
        'closed_deals_count': closed_deals_count,
        'closed_deals_sum': closed_deals_sum,
        'views_by_day': views_by_day,
        'top_properties': top_properties,
        'agents_stats': agents_stats,
        'thirty_days_ago': thirty_days_ago,
    })