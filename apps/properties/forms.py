from django import forms
from django.forms import inlineformset_factory

from .models import Property, PropertyFeature


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
            'price',
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

    # Структура формы: секция → поля → ширина bootstrap-колонки.
    # Вынесено сюда, чтобы шаблон рендерил поля циклом и разметка
    # вывода ошибок не дублировалась 22 раза.
    # Чекбоксы is_published/is_exclusive не входят — у них своя вёрстка.
    FIELDSETS = [
        ('main', 'Основное', [
            ('deal_type', 'col-md-4'),
            ('property_type', 'col-md-4'),
            ('status', 'col-md-4'),
            ('title', 'col-12'),
            ('description', 'col-12'),
        ]),
        ('price', 'Цена и комиссия', [
            ('price', 'col-md-4'),
            ('commission_percent', 'col-md-4'),
            ('commission_fixed', 'col-md-4'),
        ]),
        ('area', 'Площади и этажность', [
            ('area_total', 'col-md-3'),
            ('area_living', 'col-md-3'),
            ('area_kitchen', 'col-md-3'),
            ('rooms_count', 'col-md-3'),
            ('floor', 'col-md-3'),
            ('floors_total', 'col-md-3'),
        ]),
        ('address', 'Адрес', [
            ('city', 'col-md-4'),
            ('district', 'col-md-4'),
            ('street', 'col-md-4'),
            ('building', 'col-md-3'),
            ('apartment', 'col-md-3'),
            ('latitude', 'col-md-3'),
            ('longitude', 'col-md-3'),
        ]),
    ]

    def fieldsets(self):
        for slug, title, items in self.FIELDSETS:
            yield {
                'slug': slug,
                'title': title,
                'fields': [(self[name], css) for name, css in items],
            }

   
# Характеристики с предустановленными вариантами значений
FEATURE_CHOICES = {
    'Тип дома': [
        'Панельный', 'Кирпичный', 'Монолитный',
        'Монолитно-кирпичный', 'Блочный', 'Деревянный',
    ],
    'Санузел': [
        'Раздельный', 'Совмещённый', '2 санузла', '3 и более санузла',
    ],
    'Балкон': [
        'Нет', 'Балкон', 'Лоджия', '2 балкона', 'Балкон и лоджия',
    ],
    'Лифт': [
        'Нет', 'Пассажирский', 'Грузовой', 'Пассажирский и грузовой',
    ],
    'Парковка': [
        'Нет', 'Подземная', 'Наземная', 'Многоуровневая', 'На улице',
    ],
    'Отопление': [
        'Центральное', 'Индивидуальное', 'Газовое', 'Электрическое', 'Нет',
    ],
    'Ремонт': [
        'Без ремонта', 'Требует ремонта', 'Косметический',
        'Евроремонт', 'Дизайнерский', 'Черновая отделка',
    ],
    'Окна': [
        'Во двор', 'На улицу', 'На обе стороны', 'Панорамные',
    ],
    'Интернет': [
        'Нет', 'Есть', 'Оптоволокно',
    ],
    'Мебель': [
        'Без мебели', 'Частично', 'Полностью меблирована', 'Кухня',
    ],
    'Тип перекрытий': [
        'Железобетонные', 'Деревянные', 'Смешанные',
    ],
    'Высота потолков': [
        'До 2.5 м', '2.5 – 2.7 м', '2.7 – 3 м', 'Более 3 м',
    ],
    'Газ': [
        'Есть', 'Нет',
    ],
    'Мусоропровод': [
        'Есть', 'Нет',
    ],
}

# Список ключей в нужном порядке
FEATURE_TEMPLATES = list(FEATURE_CHOICES.keys())

class PropertyFeatureForm(forms.ModelForm):
    """Форма одной характеристики объекта.
    Виджет выбирается динамически — для известных характеристик
    показываем выпадающий список, для остальных — текстовое поле.
    """

    class Meta:
        model = PropertyFeature
        fields = ['key', 'value']
        widgets = {
            'key': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'readonly': True,
            }),
            'value': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
            }),
        }
        labels = {
            'key': 'Характеристика',
            'value': 'Значение',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Если у этой характеристики есть предустановленные варианты —
        # меняем виджет на Select
        key = None
        if self.instance and self.instance.pk:
            key = self.instance.key
        elif self.initial.get('key'):
            key = self.initial['key']

        if key and key in FEATURE_CHOICES:
            choices = [('', '— Выберите —')] + [
                (v, v) for v in FEATURE_CHOICES[key]
            ]
            self.fields['value'].widget = forms.Select(
                attrs={'class': 'form-select form-select-sm'},
                choices=choices,
            )

# Formset для редактирования нескольких характеристик одновременно
PropertyFeatureFormSet = inlineformset_factory(
    parent_model=Property,
    model=PropertyFeature,
    form=PropertyFeatureForm,
    extra=0,        # не добавлять пустые строки автоматически
    can_delete=True,
)