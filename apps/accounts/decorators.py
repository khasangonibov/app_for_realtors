"""
Декораторы для проверки доступа в CRM.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

from .models import UserProfile


def crm_required(view_func):
    """Декоратор — пропускает только сотрудников агентства.
    Клиентам (CLIENT) доступ закрыт даже если они авторизованы.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Сначала проверяем авторизацию
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        # Проверяем что пользователь не клиент
        if request.user.role == UserProfile.Role.CLIENT:
            messages.error(
                request,
                'Доступ в CRM закрыт для внешних пользователей.'
            )
            return redirect('accounts:login')

        # Проверяем что у пользователя есть агентство
        if not request.user.agency:
            messages.error(
                request,
                'Ваш аккаунт не привязан к агентству. '
                'Обратитесь к администратору.'
            )
            return redirect('accounts:login')

        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """Декоратор — только для admin и manager."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        if request.user.role not in [
            UserProfile.Role.ADMIN,
            UserProfile.Role.MANAGER,
        ]:
            messages.error(request, 'Недостаточно прав.')
            return redirect('accounts:dashboard')

        return view_func(request, *args, **kwargs)
    return wrapper