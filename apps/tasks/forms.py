from django import forms
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
            'contact': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Выберите контакт...',
            }),
            'related_property': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Выберите объект...',
            }),
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

    def __init__(self, *args, agency=None, **kwargs):
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