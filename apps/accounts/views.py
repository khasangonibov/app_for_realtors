from django.contrib.auth import login, views as auth_views
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from apps.accounts.decorators import crm_required, manager_required
from apps.chat.views import (
    get_or_create_room,
    client_chat_list as _client_chat_list,
    client_chat as _client_chat,
    client_chat_poll as _client_chat_poll,
)

from .models import User, UserProfile



@crm_required
def dashboard(request):
    """Главная страница CRM — статистика и виджеты."""
    from apps.properties.models import Property, PropertyView
    from apps.contacts.models import Contact
    from apps.deals.models import Deal
    from apps.tasks.models import Task
    from django.db.models import Count, Sum
    from datetime import timedelta

    agency = request.user.agency
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59)
    week_start = today_start - timedelta(days=today_start.weekday())
    thirty_days_ago = now - timedelta(days=30)

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

    # ── Виджеты ───────────────────────────────────────────────────────────
    stats = {
        'properties_active': properties_qs.filter(status='active').count(),
        'properties_draft': properties_qs.filter(status='draft').count(),
        'contacts_new': contacts_qs.filter(status='new').count(),
        'contacts_in_progress': contacts_qs.filter(status='in_progress').count(),
        'deals_active': deals_qs.exclude(
            stage__in=['closed', 'cancelled']
        ).count(),
        'tasks_today': tasks_qs.filter(
            is_done=False,
            due_date__range=(today_start, today_end),
        ).count(),
        'tasks_overdue': tasks_qs.filter(
            is_done=False,
            due_date__lt=now,
        ).count(),
    }

    # ── Просроченные задачи ───────────────────────────────────────────────
    overdue_tasks = tasks_qs.filter(
        is_done=False,
        due_date__lt=now,
    ).select_related('contact').order_by('due_date')[:5]

    # ── Задачи на эту неделю для календаря ───────────────────────────────
    week_tasks = tasks_qs.filter(
        is_done=False,
        due_date__gte=week_start,
        due_date__lte=week_start + timedelta(days=7),
    ).select_related('contact').order_by('due_date')

    # Группируем задачи по дням недели (0=пн, 6=вс)
    calendar_days = []
    day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_tasks = [t for t in week_tasks
                     if t.due_date.date() == day.date()]
        calendar_days.append({
            'name': day_names[i],
            'date': day,
            'tasks': day_tasks,
            'is_today': day.date() == now.date(),
        })

    # ── Мини-канбан сделок ────────────────────────────────────────────────
    active_deals = deals_qs.exclude(
        stage__in=['closed', 'cancelled']
    ).select_related('property', 'buyer_contact').order_by('created_at')

    deals_by_stage = {}
    stage_order = ['negotiation', 'deposit', 'documents', 'registration']
    stage_labels = dict(Deal.Stage.choices)
    for stage in stage_order:
        deals_by_stage[stage] = {
            'label': stage_labels.get(stage, stage),
            'deals': [d for d in active_deals if d.stage == stage],
        }

    # ── Статистика просмотров моих объектов ───────────────────────────────
    my_properties_views = PropertyView.objects.filter(
        property__in=properties_qs,
        viewed_at__gte=thirty_days_ago,
    ).count()

    # Топ объектов по просмотрам
    top_viewed = properties_qs.annotate(
        views_count=Count('views')
    ).filter(views_count__gt=0).order_by('-views_count')[:5]

    # ── Последние контакты ────────────────────────────────────────────────
    recent_contacts = contacts_qs.order_by('-created_at')[:5]

    # ── Последние объекты ─────────────────────────────────────────────────
    recent_properties = properties_qs.order_by(
        '-created_at'
    ).prefetch_related('photos')[:6]

    return render(request, 'accounts/dashboard.html', {
        'stats': stats,
        'overdue_tasks': overdue_tasks,
        'calendar_days': calendar_days,
        'deals_by_stage': deals_by_stage,
        'my_properties_views': my_properties_views,
        'top_viewed': top_viewed,
        'recent_contacts': recent_contacts,
        'recent_properties': recent_properties,
        'now': now,
    })
    
def _check_manager_access(user):
    """Проверяет что пользователь admin или manager."""
    return user.role in [UserProfile.Role.ADMIN, UserProfile.Role.MANAGER]


@crm_required
@manager_required
def users_list(request):
    users = User.objects.filter(
        agency=request.user.agency
    ).select_related('profile').order_by('last_name', 'first_name')

    return render(request, 'accounts/users_list.html', {
        'users': users,
    })


@crm_required
@manager_required
def user_invite(request):
    from .models import Agency

    if request.method == 'POST':
        from .forms import UserInviteForm
        form = UserInviteForm(request.POST, current_user=request.user)
        if form.is_valid():
            selected_role = form.cleaned_data['role']

            # Серверная защита — даже если роль admin как-то попала в POST,
            # не-суперпользователь не может её назначить
            if selected_role == UserProfile.Role.ADMIN and not request.user.is_superuser:
                messages.error(request, 'Только суперпользователь может назначать роль администратора.')
                return redirect('accounts:users_list')

            temp_password = get_random_string(12)
            user = form.save(commit=False)
            user.username = form.cleaned_data['email']
            user.agency = Agency.get_solo()
            user.set_password(temp_password)
            user.save()
            UserProfile.objects.create(
                user=user,
                role=selected_role,
            )
            messages.success(
                request,
                f'Сотрудник {user.get_full_name()} создан. '
                f'Логин: {user.email}. Временный пароль: {temp_password}'
            )
            return redirect('accounts:users_list')
    else:
        from .forms import UserInviteForm
        form = UserInviteForm(current_user=request.user)

    return render(request, 'accounts/user_invite.html', {
        'form': form,
        'title': 'Пригласить сотрудника',
    })


@crm_required
@manager_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk, agency=request.user.agency)

    # Не-суперпользователь не может редактировать администратора вообще —
    # ни его роль, ни другие данные, чтобы исключить случайное понижение
    target_is_admin = hasattr(user, 'profile') and user.profile.role == UserProfile.Role.ADMIN
    if target_is_admin and not request.user.is_superuser:
        messages.error(request, 'Редактировать администратора может только суперпользователь.')
        return redirect('accounts:users_list')

    if request.method == 'POST':
        from .forms import UserEditForm
        form = UserEditForm(request.POST, instance=user, current_user=request.user)
        if form.is_valid():
            selected_role = form.cleaned_data['role']

            if selected_role == UserProfile.Role.ADMIN and not request.user.is_superuser:
                messages.error(request, 'Только суперпользователь может назначать роль администратора.')
                return redirect('accounts:users_list')

            form.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = selected_role
            profile.save()
            messages.success(request, 'Данные сотрудника обновлены.')
            return redirect('accounts:users_list')
    else:
        from .forms import UserEditForm
        initial_role = user.profile.role if hasattr(user, 'profile') else UserProfile.Role.AGENT
        form = UserEditForm(instance=user, current_user=request.user, initial={'role': initial_role})

    return render(request, 'accounts/user_invite.html', {
        'form': form,
        'edit_user': user,
        'title': f'Редактировать: {user.get_full_name()}',
    })


@crm_required
@manager_required
def user_toggle_active(request, pk):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk, agency=request.user.agency)

        if user == request.user:
            messages.error(request, 'Нельзя деактивировать свой аккаунт.')
            return redirect('accounts:users_list')

        target_is_admin = hasattr(user, 'profile') and user.profile.role == UserProfile.Role.ADMIN
        if target_is_admin and not request.user.is_superuser:
            messages.error(request, 'Изменять статус администратора может только суперпользователь.')
            return redirect('accounts:users_list')

        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        status = 'активирован' if user.is_active else 'деактивирован'
        messages.success(request, f'Сотрудник {user.get_full_name()} {status}.')
    return redirect('accounts:users_list')


@crm_required
@manager_required
def user_reset_password(request, pk):
    if request.method == 'POST':
        from django.utils.crypto import get_random_string
        user = get_object_or_404(User, pk=pk, agency=request.user.agency)

        target_is_admin = hasattr(user, 'profile') and user.profile.role == UserProfile.Role.ADMIN
        if target_is_admin and not request.user.is_superuser:
            messages.error(request, 'Сбросить пароль администратора может только суперпользователь.')
            return redirect('accounts:users_list')

        temp_password = get_random_string(12)
        user.set_password(temp_password)
        user.save()
        messages.success(
            request,
            f'Новый пароль для {user.get_full_name()}: {temp_password}'
        )
    return redirect('accounts:users_list')


@never_cache
def client_register(request):
    """Регистрация внешнего пользователя (клиента)."""
    from .forms import ClientRegisterForm
    from apps.contacts.models import Contact
    from apps.accounts.models import Agency

    if request.user.is_authenticated:
        return redirect('public:catalog')

    if request.method == 'POST':
        form = ClientRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(
                user=user,
                role=UserProfile.Role.CLIENT,
            )

            agency = Agency.get_solo()
            if agency:
                Contact.objects.get_or_create(
                    email=user.email,
                    agency=agency,
                    defaults={
                        'first_name': user.first_name or user.username,
                        'last_name': user.last_name or '',
                        'phone': user.phone or '',
                        'contact_type': Contact.ContactType.BUYER,
                        'status': Contact.Status.NEW,
                        'source': Contact.Source.SITE,
                        'notes': 'Зарегистрировался через публичный сайт.',
                    }
                )

            login(request, user)
            messages.success(
                request,
                f'Добро пожаловать, {user.first_name}! '
                f'Вы успешно зарегистрировались.'
            )
            return redirect('public:profile')
    else:
        form = ClientRegisterForm()

    return render(request, 'public/register.html', {'form': form})


@login_required
def client_profile(request):
    """Личный кабинет клиента."""
    from apps.selections.models import Selection
    from apps.contacts.models import Contact
    from apps.chat.models import ChatRoom, Message

    contacts = Contact.objects.filter(email=request.user.email)

    selections = Selection.objects.filter(
        contact__in=contacts
    ).prefetch_related('items__property').order_by('-created_at')

    # Чаты клиента с подсчётом непрочитанных
    rooms = ChatRoom.objects.filter(
        client=request.user,
    ).select_related('agent').prefetch_related('messages')

    rooms_with_info = []
    for room in rooms:
        unread = room.messages.filter(
            is_read=False,
        ).exclude(sender=request.user).count()
        last_msg = room.messages.order_by('-created_at').first()
        rooms_with_info.append({
            'room': room,
            'unread': unread,
            'last_message': last_msg,
        })

    # Сортируем — сначала с непрочитанными и последними сообщениями
    rooms_with_info.sort(key=lambda x: (
        -x['unread'],
        -(x['last_message'].created_at.timestamp()
          if x['last_message'] else 0)
    ))

    return render(request, 'public/profile.html', {
        'selections': selections,
        'contacts': contacts,
        'rooms': rooms_with_info,
    })

@method_decorator(never_cache, name='dispatch')
class PublicLoginView(auth_views.LoginView):
    """Универсальная страница входа — для клиентов и сотрудников."""
    template_name = 'public/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        # Клиенты → личный кабинет
        if hasattr(user, 'profile') and user.profile.role == UserProfile.Role.CLIENT:
            return '/profile/'
        # Все остальные (admin, manager, agent) → CRM
        return '/crm/'

    def form_valid(self, form):
        """Проверяем что аккаунт активен."""
        user = form.get_user()
        if not user.is_active:
            form.add_error(None, 'Аккаунт деактивирован. Обратитесь к администратору.')
            return self.form_invalid(form)
        return super().form_valid(form)
    
    
def client_chat_list(request):
    return _client_chat_list(request)

def client_chat(request, room_pk=None, agent_pk=None):
    return _client_chat(request, room_pk=room_pk, agent_pk=agent_pk)

def client_chat_poll(request, room_pk):
    return _client_chat_poll(request, room_pk=room_pk)