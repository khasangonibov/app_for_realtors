from django.contrib.auth import login, views as auth_views
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.crypto import get_random_string

from apps.accounts.decorators import crm_required, manager_required

from .forms import CRMLoginForm
from .models import User, UserProfile

class CRMLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    form_class = CRMLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        """После успешной проверки логина/пароля — проверяем роль."""
        user = form.get_user()
        # Клиентам (внешним пользователям) вход в CRM закрыт
        if user.role == UserProfile.Role.CLIENT:
            form.add_error(
                None,
                'Доступ в CRM закрыт для внешних пользователей.'
            )
            return self.form_invalid(form)
        return super().form_valid(form)


class CRMLogoutView(auth_views.LogoutView):
    pass


@crm_required
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
    if request.method == 'POST':
        from .forms import UserInviteForm
        form = UserInviteForm(request.POST)
        if form.is_valid():
            from django.utils.crypto import get_random_string
            temp_password = get_random_string(12)
            user = form.save(commit=False)
            user.agency = request.user.agency
            user.set_password(temp_password)
            user.save()
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


@crm_required
@manager_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk, agency=request.user.agency)

    if request.method == 'POST':
        from .forms import UserEditForm
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
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


@crm_required
@manager_required
def user_toggle_active(request, pk):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk, agency=request.user.agency)
        if user == request.user:
            messages.error(request, 'Нельзя деактивировать свой аккаунт.')
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
        temp_password = get_random_string(12)
        user.set_password(temp_password)
        user.save()
        messages.success(
            request,
            f'Новый пароль для {user.get_full_name()}: {temp_password}'
        )
    return redirect('accounts:users_list')



def client_register(request):
    """Регистрация внешнего пользователя (клиента)."""
    from .forms import ClientRegisterForm

    if request.user.is_authenticated:
        return redirect('public:catalog')

    if request.method == 'POST':
        form = ClientRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Создаём профиль с ролью CLIENT
            UserProfile.objects.create(
                user=user,
                role=UserProfile.Role.CLIENT,
            )

            # Автоматически создаём Contact во всех агентствах
            # чтобы риелторы могли найти клиента и привязать подборку
            # Берём первое активное агентство (или можно выбирать конкретное)
            from apps.contacts.models import Contact
            from apps.accounts.models import Agency

            # Создаём контакт без привязки к конкретному агентству —
            # риелтор сам найдёт по email и привяжет к своему агентству
            # Либо создаём в агентстве которое указано в запросе (если сайт одного агентства)
            agency = Agency.objects.first()  # для одноагентской системы
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

def client_profile(request):
    """Личный кабинет клиента — список его подборок."""
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    from apps.selections.models import Selection

    # Подборки привязанные к контакту этого пользователя
    # Ищем контакт по email пользователя
    from apps.contacts.models import Contact
    contacts = Contact.objects.filter(email=request.user.email)

    selections = Selection.objects.filter(
        contact__in=contacts
    ).prefetch_related('items__property').order_by('-created_at')

    return render(request, 'public/profile.html', {
        'selections': selections,
        'contacts': contacts,
    })


class PublicLoginView(auth_views.LoginView):
    """Логин для публичной части — клиенты."""
    template_name = 'public/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        # Если роль не CLIENT — редиректим в CRM
        if user.role != UserProfile.Role.CLIENT:
            return '/crm/'
        return '/profile/'