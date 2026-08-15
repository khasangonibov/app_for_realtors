from django import forms
from apps.accounts.models import User
from .models import Task


class TaskForm(forms.ModelForm):

    class Meta:
        model = Task
        fields = [
            'title', 'task_type', 'priority',
            'due_date', 'contact', 'related_property',
            'description',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'contact': forms.Select(attrs={'class': 'form-select select2'}),
            'related_property': forms.Select(attrs={'class': 'form-select select2'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
            }),
        }
        labels = {
            'title': 'Название задачи',
            'task_type': 'Тип',
            'priority': 'Приоритет',
            'due_date': 'Срок выполнения',
            'contact': 'Контакт',
            'related_property': 'Объект',
            'description': 'Описание',
        }

    def __init__(self, *args, agency=None, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contact'].required = False
        self.fields['contact'].empty_label = 'Без контакта'
        self.fields['related_property'].required = False
        self.fields['related_property'].empty_label = 'Без объекта'

        if agency:
            self.fields['contact'].queryset = \
                self.fields['contact'].queryset.filter(agency=agency)
            self.fields['related_property'].queryset = \
                self.fields['related_property'].queryset.filter(agency=agency)

        # Поле выбора исполнителя — видно только менеджеру/админу
        if current_user and not current_user.is_agent:
            self.fields['agent'] = forms.ModelChoiceField(
                queryset=User.objects.filter(agency=agency, is_active=True),
                label='Исполнитель',
                required=True,
                initial=current_user,
                widget=forms.Select(attrs={'class': 'form-select select2'}),
            )
            # Переупорядочиваем поля — исполнитель сразу после названия
            field_order = ['title', 'agent', 'task_type', 'priority',
                            'due_date', 'contact', 'related_property', 'description']
            self.order_fields(field_order)
            
            
class TaskCompletionForm(forms.Form):
    """Форма комментария при отметке задачи выполненной."""
    comment = forms.CharField(
        label='Комментарий к выполнению',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Кратко опишите что сделано...',
        }),
        required=True,
    )