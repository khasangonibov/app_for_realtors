from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.crypto import get_random_string

from .forms import CRMLoginForm
from .models import User, UserProfile

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
    
def _check_manager_access(user):
    """Проверяет что пользователь admin или manager."""
    return user.role in [UserProfile.Role.ADMIN, UserProfile.Role.MANAGER]


@login_required
def users_list(request):
    """Список сотрудников агентства."""
    if not _check_manager_access(request.user):
        messages.error(request, 'Недостаточно прав.')
        return redirect('accounts:dashboard')

    users = User.objects.filter(
        agency=request.user.agency
    ).select_related('profile').order_by('last_name', 'first_name')

    return render(request, 'accounts/users_list.html', {
        'users': users,
    })


@login_required
def user_invite(request):
    """Приглашение нового сотрудника — создаём аккаунт с временным паролем."""
    if not _check_manager_access(request.user):
        messages.error(request, 'Недостаточно прав.')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        from .forms import UserInviteForm
        form = UserInviteForm(request.POST)
        if form.is_valid():
            # Генерируем временный пароль
            temp_password = get_random_string(12)

            user = form.save(commit=False)
            user.agency = request.user.agency
            user.set_password(temp_password)
            user.save()

            # Создаём профиль с выбранной ролью
            UserProfile.objects.create(
                user=user,
                role=form.cleaned_data['role'],
            )

            messages.success(
                request,
                f'Сотрудник {user.get_full_name()} создан. '
                f'Временный пароль: {temp_password}'
            )
            return redirect('accounts:users_list')
    else:
        from .forms import UserInviteForm
        form = UserInviteForm()

    return render(request, 'accounts/user_invite.html', {
        'form': form,
        'title': 'Пригласить сотрудника',
    })


@login_required
def user_edit(request, pk):
    """Редактирование роли и данных сотрудника."""
    if not _check_manager_access(request.user):
        messages.error(request, 'Недостаточно прав.')
        return redirect('accounts:dashboard')

    user = get_object_or_404(
        User, pk=pk, agency=request.user.agency
    )

    if request.method == 'POST':
        from .forms import UserEditForm
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            # Обновляем роль
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = form.cleaned_data['role']
            profile.save()
            messages.success(request, 'Данные сотрудника обновлены.')
            return redirect('accounts:users_list')
    else:
        from .forms import UserEditForm
        initial_role = user.profile.role if hasattr(user, 'profile') else UserProfile.Role.AGENT
        form = UserEditForm(instance=user, initial={'role': initial_role})

    return render(request, 'accounts/user_invite.html', {
        'form': form,
        'edit_user': user,
        'title': f'Редактировать: {user.get_full_name()}',
    })


@login_required
def user_toggle_active(request, pk):
    """Активировать/деактивировать сотрудника."""
    if not _check_manager_access(request.user):
        messages.error(request, 'Недостаточно прав.')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        user = get_object_or_404(
            User, pk=pk, agency=request.user.agency
        )
        # Нельзя деактивировать самого себя
        if user == request.user:
            messages.error(request, 'Нельзя деактивировать свой аккаунт.')
            return redirect('accounts:users_list')

        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        status = 'активирован' if user.is_active else 'деактивирован'
        messages.success(request, f'Сотрудник {user.get_full_name()} {status}.')

    return redirect('accounts:users_list')


@login_required
def user_reset_password(request, pk):
    """Сброс пароля сотрудника — генерируем новый временный пароль."""
    if not _check_manager_access(request.user):
        messages.error(request, 'Недостаточно прав.')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        user = get_object_or_404(
            User, pk=pk, agency=request.user.agency
        )
        temp_password = get_random_string(12)
        user.set_password(temp_password)
        user.save()
        messages.success(
            request,
            f'Новый пароль для {user.get_full_name()}: {temp_password}'
        )

    return redirect('accounts:users_list')