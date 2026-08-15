from django import forms
from .models import Deal
from apps.accounts.models import User



class DealForm(forms.ModelForm):

    class Meta:
        model = Deal
        fields = [
            'property', 'stage',
            'seller_contact', 'buyer_contact',
            'price_agreed', 'commission_total',
            'deposit_amount', 'deposit_date',
            'contract_date', 'close_date',
            'notes',
        ]
        widgets = {
            'property': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Выберите объект...',
            }),
            'stage': forms.Select(attrs={'class': 'form-select'}),
            'seller_contact': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Выберите продавца...',
            }),
            'buyer_contact': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Выберите покупателя...',
            }),
            'price_agreed': forms.NumberInput(attrs={'class': 'form-control'}),
            'commission_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'deposit_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'contract_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'close_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'property': 'Объект',
            'stage': 'Стадия',
            'seller_contact': 'Продавец',
            'buyer_contact': 'Покупатель',
            'price_agreed': 'Согласованная цена, ₽',
            'commission_total': 'Комиссия итого, ₽',
            'deposit_amount': 'Задаток, ₽',
            'deposit_date': 'Дата задатка',
            'contract_date': 'Дата договора',
            'close_date': 'Дата закрытия',
            'notes': 'Заметки',
        }

    def __init__(self, *args, agency=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Показываем только объекты и контакты своего агентства
        if agency:
            self.fields['property'].queryset = \
                self.fields['property'].queryset.filter(agency=agency)
            self.fields['seller_contact'].queryset = \
                self.fields['seller_contact'].queryset.filter(agency=agency)
            self.fields['buyer_contact'].queryset = \
                self.fields['buyer_contact'].queryset.filter(agency=agency)
                
                
class DealFilterForm(forms.Form):
    """Форма фильтрации сделок на kanban-доске."""
    stage = forms.ChoiceField(
        label='Стадия',
        choices=[('', 'Все стадии')] + list(Deal.Stage.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    agent = forms.ModelChoiceField(
        label='Риелтор',
        queryset=User.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm select2'}),
    )
    search = forms.CharField(
        label='Поиск',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Объект, покупатель, продавец...',
        }),
    )

    def __init__(self, *args, agency=None, **kwargs):
        super().__init__(*args, **kwargs)
        if agency:
            self.fields['agent'].queryset = User.objects.filter(
                agency=agency, is_active=True,
            )
        self.fields['agent'].empty_label = 'Все риелторы'