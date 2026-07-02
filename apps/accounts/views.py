from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from .forms import CRMLoginForm


class CRMLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    form_class = CRMLoginForm
    redirect_authenticated_user = True


class CRMLogoutView(auth_views.LogoutView):
    pass


@login_required
def dashboard(request):
    """Главная страница CRM — статистика и виджеты."""
    from apps.properties.models import Property
    from apps.contacts.models import Contact
    from apps.deals.models import Deal
    from apps.tasks.models import Task

    agency = request.user.agency
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Базовые фильтры — риелтор видит своё, менеджер/admin — всё агентства
    if request.user.is_agent:
        properties_qs = Property.objects.filter(agency=agency, agent=request.user)
        contacts_qs = Contact.objects.filter(agency=agency, agent=request.user)
        deals_qs = Deal.objects.filter(agency=agency, agent=request.user)
        tasks_qs = Task.objects.filter(agency=agency, agent=request.user)
    else:
        properties_qs = Property.objects.filter(agency=agency)
        contacts_qs = Contact.objects.filter(agency=agency)
        deals_qs = Deal.objects.filter(agency=agency)
        tasks_qs = Task.objects.filter(agency=agency, agent=request.user)

    # ── Виджеты (счётчики) ────────────────────────────────────────────────
    stats = {
        # Объекты
        'properties_active': properties_qs.filter(status='active').count(),
        'properties_draft': properties_qs.filter(status='draft').count(),

        # Контакты
        'contacts_new': contacts_qs.filter(status='new').count(),
        'contacts_in_progress': contacts_qs.filter(status='in_progress').count(),

        # Сделки
        'deals_active': deals_qs.exclude(
            stage__in=['closed', 'cancelled']
        ).count(),

        # Задачи
        'tasks_today': tasks_qs.filter(
            is_done=False,
            due_date__range=(today_start, today_end),
        ).count(),
        'tasks_overdue': tasks_qs.filter(
            is_done=False,
            due_date__lt=now,
        ).count(),
    }

    # ── Списки для виджетов ───────────────────────────────────────────────
    overdue_tasks = tasks_qs.filter(
        is_done=False,
        due_date__lt=now,
    ).select_related('contact').order_by('due_date')[:5]

    recent_contacts = contacts_qs.order_by('-created_at')[:5]

    recent_properties = properties_qs.order_by(
        '-created_at'
    ).prefetch_related('photos')[:6]

    return render(request, 'accounts/dashboard.html', {
        'stats': stats,
        'overdue_tasks': overdue_tasks,
        'recent_contacts': recent_contacts,
        'recent_properties': recent_properties,
        'now': now,
    })