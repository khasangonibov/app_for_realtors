apps/properties/
├── __init__.py
├── apps.py
├── admin.py
├── models.py          
├── urls/
│   ├── __init__.py
│   ├── public.py       # публичные URL (карточка объекта)
│   └── crm.py           # CRM URL (список, редактирование)
├── views/
│   ├── __init__.py
│   ├── public.py
│   └── crm.py
├── forms.py
├── api_urls.py
├── serializers.py
└── templates/
    └── properties/
        ├── public_detail.html   # публичная карточка
        └── crm/
            ├── list.html
            ├── detail.html
            └── form.html