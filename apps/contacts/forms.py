from django import forms
from .models import Contact, ContactActivity


class ContactForm(forms.ModelForm):
    """Форма создания и редактирования контакта."""

    class Meta:
        model = Contact
        fields = [
            'last_name', 'first_name', 'middle_name',
            'phone', 'email',
            'contact_type', 'status', 'source',
            'budget_min', 'budget_max',
            'notes',
        ]
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 999-99-99'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'budget_min': forms.NumberInput(attrs={'class': 'form-control'}),
            'budget_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'last_name': 'Фамилия',
            'first_name': 'Имя',
            'middle_name': 'Отчество',
            'phone': 'Телефон',
            'email': 'Email',
            'contact_type': 'Тип клиента',
            'status': 'Статус',
            'source': 'Источник',
            'budget_min': 'Бюджет от, ₽',
            'budget_max': 'Бюджет до, ₽',
            'notes': 'Заметки',
        }


class ActivityForm(forms.ModelForm):
    """Форма добавления активности (звонок, встреча, заметка)
    прямо на странице контакта.
    """

    class Meta:
        model = ContactActivity
        fields = ['activity_type', 'description', 'scheduled_at']
        widgets = {
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Опишите что произошло или что запланировано...',
            }),
            'scheduled_at': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }
        labels = {
            'activity_type': 'Тип',
            'description': 'Описание',
            'scheduled_at': 'Дата и время (для задач)',
        }