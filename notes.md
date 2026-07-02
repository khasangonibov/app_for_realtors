app for realtors/                ← корень проекта
│
├── apps/                        ← все наши приложения
│   │
│   └── accounts/                ← модуль пользователей
│       ├── __init__.py          ← пустой, делает папку пакетом Python
│       ├── apps.py              ← конфиг приложения (название, verbose_name)
│       ├── models.py            ← модели: Agency, User, UserProfile
│       ├── admin.py             ← регистрация моделей в Django-админке
│       ├── forms.py             ← формы: логин, редактирование профиля
│       ├── views.py             ← обработчики запросов
│       ├── urls.py              ← маршруты /crm/login/, /crm/profile/ и т.д.
│       ├── context_processors.py← добавляет данные агентства во все шаблоны
│       ├── api_urls.py          ← маршруты REST API /api/v1/users/
│       ├── serializers.py       ← DRF сериализаторы для API
│       └── templates/
│           └── accounts/
│               ├── login.html
│               ├── profile.html
│               └── users_list.html
│
├── config/
│    ├── __init__.py      ← импортирует celery app
│    ├── celery.py        ← настройка Celery
│    ├── urls.py          ← главный роутер
│    └── settings/
│        ├── __init__.py
│        ├── base.py
│        ├── development.py
│        └── production.py
├── templates/
├── static/
├── manage.py
└── .env