"""
Формы приложения accounts.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CRMLoginForm(AuthenticationForm):
    """Форма входа в CRM.

    Наследуем стандартную AuthenticationForm от Django — она уже
    умеет проверять логин/пароль. Переопределяем только виджеты,
    чтобы добавить Bootstrap-классы для красивого отображения.
    """
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите логин',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль',
        })
    )