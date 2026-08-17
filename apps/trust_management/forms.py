from django import forms
from django.db import models
from .models import ManagementContract, Transaction, ManagementDocument


class ManagementContractForm(forms.ModelForm):

    class Meta:
        model = ManagementContract
        fields = [
            'related_property', 'owner', 'agent',
            'contract_number', 'status',
            'start_date', 'end_date',
            'commission_type', 'commission_percent', 'commission_fixed',
            'terms',
        ]
        widgets = {
            'related_property': forms.Select(attrs={'class': 'form-select select2'}),
            'owner': forms.Select(attrs={'class': 'form-select select2'}),
            'agent': forms.Select(attrs={'class': 'form-select select2'}),
            'contract_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'end_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'commission_type': forms.Select(attrs={'class': 'form-select'}),
            'commission_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'commission_fixed': forms.NumberInput(attrs={'class': 'form-control'}),
            'terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'related_property': 'Объект',
            'owner': 'Собственник',
            'agent': 'Управляющий агент',
            'contract_number': 'Номер договора',
            'status': 'Статус',
            'start_date': 'Дата начала',
            'end_date': 'Дата окончания',
            'commission_type': 'Тип комиссии',
            'commission_percent': 'Комиссия, %',
            'commission_fixed': 'Комиссия фикс., ₽/мес',
            'terms': 'Условия договора',
        }

    def __init__(self, *args, agency=None, **kwargs):
        super().__init__(*args, **kwargs)
        if agency:
            # Только объекты своего агентства, ещё не в управлении
            qs = self.fields['related_property'].queryset.filter(agency=agency, is_deleted=False,)
            if self.instance.pk:
                # При редактировании — не исключаем текущий объект
                qs = qs.filter(
                    models.Q(management_contract__isnull=True) |
                    models.Q(pk=self.instance.related_property_id)
                )
            else:
                qs = qs.filter(management_contract__isnull=True)
            self.fields['related_property'].queryset = qs
            self.fields['owner'].queryset = self.fields['owner'].queryset.filter(agency=agency, is_deleted=False)
            self.fields['agent'].queryset = self.fields['agent'].queryset.filter(agency=agency)


class TransactionForm(forms.ModelForm):

    class Meta:
        model = Transaction
        fields = ['type', 'category', 'amount', 'date', 'description']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'type': 'Тип',
            'category': 'Категория',
            'amount': 'Сумма, ₽',
            'date': 'Дата',
            'description': 'Описание',
        }


class ManagementDocumentForm(forms.ModelForm):

    class Meta:
        model = ManagementDocument
        fields = ['doc_type', 'name', 'file']
        widgets = {
            'doc_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'doc_type': 'Тип документа',
            'name': 'Название',
            'file': 'Файл',
        }