from django import forms
from .models import Property


class PropertyFilterForm(forms.Form):
    """Форма фильтрации списка объектов в CRM.
    Все поля необязательные — риелтор может фильтровать
    по любому сочетанию параметров или не фильтровать вообще.
    """
    status = forms.ChoiceField(
        label='Статус',
        choices=[('', 'Все статусы')] + Property.Status.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    deal_type = forms.ChoiceField(
        label='Тип сделки',
        choices=[('', 'Все')] + Property.DealType.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    property_type = forms.ChoiceField(
        label='Тип объекта',
        choices=[('', 'Все типы')] + Property.PropertyType.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    city = forms.CharField(
        label='Город',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Город',
        }),
    )
    search = forms.CharField(
        label='Поиск',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Адрес, название...',
        }),
    )

class PropertyForm(forms.ModelForm):
    """Форма создания и редактирования объекта недвижимости.
    Используется в CRM риелтором — не в Django Admin.
    ModelForm автоматически строит поля из модели,
    мы только переопределяем виджеты для Bootstrap-стилей.
    """

    class Meta:
        model = Property
        fields = [
            # Тип сделки и объекта
            'deal_type', 'property_type', 'status',
            # Описание
            'title', 'description',
            # Цена
            'price', 'price_currency',
            'commission_percent', 'commission_fixed',
            # Площади
            'area_total', 'area_living', 'area_kitchen',
            'rooms_count', 'floor', 'floors_total',
            # Адрес
            'city', 'district', 'street', 'building', 'apartment',
            # Координаты
            'latitude', 'longitude',
            # Публикация
            'is_published', 'is_exclusive',
        ]
        # agent и agency не включаем в форму —
        # они проставляются автоматически во view

        widgets = {
            'deal_type': forms.Select(attrs={'class': 'form-select'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Уютная квартира в центре'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'price_currency': forms.TextInput(attrs={'class': 'form-control'}),
            'commission_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'commission_fixed': forms.NumberInput(attrs={'class': 'form-control'}),
            'area_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'area_living': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'area_kitchen': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'rooms_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'floor': forms.NumberInput(attrs={'class': 'form-control'}),
            'floors_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'street': forms.TextInput(attrs={'class': 'form-control'}),
            'building': forms.TextInput(attrs={'class': 'form-control'}),
            'apartment': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_exclusive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

        labels = {
            'deal_type': 'Тип сделки',
            'property_type': 'Тип объекта',
            'status': 'Статус',
            'title': 'Заголовок',
            'description': 'Описание',
            'price': 'Цена, ₽',
            'price_currency': 'Валюта',
            'commission_percent': 'Комиссия, %',
            'commission_fixed': 'Комиссия фикс., ₽',
            'area_total': 'Общая площадь, м²',
            'area_living': 'Жилая площадь, м²',
            'area_kitchen': 'Площадь кухни, м²',
            'rooms_count': 'Количество комнат',
            'floor': 'Этаж',
            'floors_total': 'Этажей в доме',
            'city': 'Город',
            'district': 'Район',
            'street': 'Улица',
            'building': 'Дом',
            'apartment': 'Квартира/офис',
            'latitude': 'Широта',
            'longitude': 'Долгота',
            'is_published': 'Опубликован публично',
            'is_exclusive': 'Эксклюзивный объект',
        } 