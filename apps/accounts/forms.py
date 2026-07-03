"""
Формы приложения accounts.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import User, UserProfile


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
    
class UserInviteForm(forms.ModelForm):
    """Форма создания нового сотрудника."""
    role = forms.ChoiceField(
        label='Роль',
        choices=UserProfile.Role.choices,
        initial=UserProfile.Role.AGENT,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 999-99-99',
            }),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'username': 'Логин',
            'email': 'Email',
            'phone': 'Телефон',
        }


class UserEditForm(forms.ModelForm):
    """Форма редактирования сотрудника."""
    role = forms.ChoiceField(
        label='Роль',
        choices=UserProfile.Role.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
            'phone': 'Телефон',
        }