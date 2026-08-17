from django import forms
from .models import Selection, SelectionItem


class SelectionForm(forms.ModelForm):

    class Meta:
        model = Selection
        fields = ['title', 'contact']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Квартиры для Ивановых',
            }),
            'contact': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Начните вводить имя или телефон...',
            }),
        }
        labels = {
            'title': 'Название подборки',
            'contact': 'Клиент',
        }

    def __init__(self, *args, agency=None, **kwargs):
        super().__init__(*args, **kwargs)
        if agency:
            self.fields['contact'].queryset = \
                self.fields['contact'].queryset.filter(agency=agency, is_deleted=False,)
        # Клиент необязателен — можно создать подборку без привязки
        self.fields['contact'].required = False
        self.fields['contact'].empty_label = 'Без клиента'


class SelectionItemForm(forms.ModelForm):
    """Форма добавления объекта в подборку."""

    class Meta:
        model = SelectionItem
        fields = ['property', 'agent_comment']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'agent_comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Почему вы рекомендуете этот объект клиенту...',
            }),
        }
        labels = {
            'property': 'Объект',
            'agent_comment': 'Комментарий для клиента',
        }

    def __init__(self, *args, agency=None, selection=None, **kwargs):
        super().__init__(*args, **kwargs)
        if agency:
            # Показываем только опубликованные объекты агентства
            qs = self.fields['property'].queryset.filter(
                agency=agency,
                is_published=True,
            )
            # Исключаем объекты уже добавленные в эту подборку
            if selection:
                already_added = selection.items.values_list('property_id', flat=True)
                qs = qs.exclude(pk__in=already_added)
            self.fields['property'].queryset = qs
        self.fields['agent_comment'].required = False