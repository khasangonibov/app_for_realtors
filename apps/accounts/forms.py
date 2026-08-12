"""
Формы приложения accounts.
"""

from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.utils.text import slugify
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password


import re
from .models import User, UserProfile


    
class UserInviteForm(forms.ModelForm):
    """Форма создания нового сотрудника. Логином служит email."""
    role = forms.ChoiceField(
        label='Роль',
        choices=UserProfile.Role.choices,
        initial=UserProfile.Role.AGENT,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 999-99-99',
            }),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
            'phone': 'Телефон',
        }

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not (current_user and current_user.is_superuser):
            self.fields['role'].choices = [
                (value, label) for value, label in UserProfile.Role.choices
                if value != UserProfile.Role.ADMIN
            ]

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError('Email обязателен — он используется как логин.')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email
    

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

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not (current_user and current_user.is_superuser):
            self.fields['role'].choices = [
                (value, label) for value, label in UserProfile.Role.choices
                if value != UserProfile.Role.ADMIN
            ]
        
class ClientRegisterForm(forms.ModelForm):
    """Форма регистрации клиента. Логином служит email —
    отдельного поля username пользователь не видит и не вводит.
    """
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Минимум 8 символов, минимум одна заглавная буква, '
                   'одна цифра и один спецсимвол.',
    )
    password2 = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 999-99-99',
            }),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
            'phone': 'Телефон',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError('Укажите email — он используется для входа.')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        if len(password) < 8:
            raise forms.ValidationError('Пароль должен быть не менее 8 символов.')
        if not re.search(r'[A-ZА-Я]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну заглавную букву.')
        if not re.search(r'\d', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну цифру.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]/~`]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы один специальный символ.')
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise forms.ValidationError(e.messages)
        return password

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Пароли не совпадают.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        # username технически нужен Django, но пользователь его не видит —
        # используем email как username, раз оба уникальны
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
    

class StyledSetPasswordForm(SetPasswordForm):
    """Форма установки нового пароля при восстановлении —
    добавляем Bootstrap-классы и ту же валидацию сложности,
    что и при регистрации.
    """
    new_password1 = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password2 = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1', '')
        if len(password) < 8:
            raise forms.ValidationError('Пароль должен быть не менее 8 символов.')
        if not re.search(r'[A-ZА-Я]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну заглавную букву.')
        if not re.search(r'\d', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну цифру.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]/~`]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы один специальный символ.')
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise forms.ValidationError(e.messages)
        return password