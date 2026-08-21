"""
Базовые настройки Django для CRM агентства недвижимости.
Этот файл содержит всё общее для dev и prod окружений.
"""

import environ
from pathlib import Path


from celery.schedules import crontab


# ─── Пути ────────────────────────────────────────────────────────────────────
# BASE_DIR указывает на корень проекта (папку realestate_crm/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─── Переменные окружения ─────────────────────────────────────────────────────
# django-environ читает .env файл и отдаёт значения через env(...)
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / '.env')


# ─── Безопасность ─────────────────────────────────────────────────────────────
SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env('DJANGO_DEBUG')
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])


# ─── Приложения ───────────────────────────────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',     # фильтры: intcomma, naturaltime и т.д.
]

THIRD_PARTY_APPS = [
    'rest_framework',              # DRF — REST API
    'rest_framework_simplejwt',    # JWT авторизация
    'corsheaders',                 # CORS заголовки
    'crispy_forms',                # красивые формы
    'crispy_bootstrap5',           # Bootstrap 5 тема для crispy
    'django_htmx',                 # интеграция HTMX с Django
    'django_celery_beat',          # расписание задач в БД
    'import_export',               # экспорт/импорт Excel
    'storages',                    # S3 хранилище
    
    # OAuth вход для клиентов
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.vk',
]

LOCAL_APPS = [
    # Наши приложения в порядке зависимостей
    'apps.core', 
    'apps.accounts',          # пользователи, агентства, роли
    'apps.properties',        # объекты недвижимости
    'apps.contacts',          # клиенты и лиды
    'apps.deals',             # сделки
    'apps.selections',        # подборки для клиентов
    'apps.tasks',             # задачи и напоминания
    'apps.analytics',         # отчёты и аналитика
    'apps.notifications',     # уведомления
    'apps.chat',              # чат
    'apps.trust_management',  # доверительное упрввление 
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ─── Middleware ────────────────────────────────────────────────────────────────
# Порядок важен! corsheaders должен быть первым.
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'


# ─── Шаблоны ──────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # папка templates/ в корне проекта
        'APP_DIRS': True,                   # Django ищет templates/ внутри каждого app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Наш кастомный процессор — добавляет данные агентства в контекст
                'apps.accounts.context_processors.agency_context',
            ],
        },
    },
]


# ─── База данных ──────────────────────────────────────────────────────────────
# dj-database-url парсит строку вида postgres://user:pass@host:port/dbname
# DATABASES = {
#     'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'realestate_crm',
        'USER': 'crm_user',
        'PASSWORD': 'crm_password',
        'HOST': 'appforrealtors-db-1',  
        'PORT': '5432',
    }
}

# Все FK и ManyToMany используют транзакции — нужен ATOMIC_REQUESTS
DATABASES['default']['ATOMIC_REQUESTS'] = True


# ─── Кэш ──────────────────────────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/0'),
    }
}


# ─── Сессии ───────────────────────────────────────────────────────────────────
# Храним сессии в Redis (быстро и можно инвалидировать)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'


# ─── Пароли ───────────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Наша кастомная модель пользователя (расширяет AbstractUser)
AUTH_USER_MODEL = 'accounts.User'

# Куда редиректить после логина/логаута
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/crm/'
LOGOUT_REDIRECT_URL = '/login/'


# ─── Локализация ──────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True     # переводы интерфейса
USE_TZ = True       # хранить даты в UTC, конвертировать при выводе


# ─── Статика и медиа ──────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'   # куда collectstatic собирает файлы
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'          # загруженные файлы (только в dev!)


# ─── S3 хранилище (для production и при USE_S3=True) ─────────────────────────
USE_S3 = env.bool('USE_S3', default=False)

if USE_S3:
    # django-storages отправляет файлы в S3/MinIO
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
        },
        'staticfiles': {
            'BACKEND': 'storages.backends.s3boto3.S3StaticStorage',
        },
    }
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = env('AWS_S3_ENDPOINT_URL', default=None)  # для MinIO
    AWS_S3_FILE_OVERWRITE = False       # не перезаписывать файлы с одинаковым именем
    AWS_DEFAULT_ACL = 'private'         # файлы закрытые по умолчанию
    AWS_S3_CUSTOM_DOMAIN = None


# ─── Email ────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@example.com')


# ─── Celery (асинхронные задачи) ──────────────────────────────────────────────
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'


# ─── Django REST Framework ─────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # для браузера
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}


# ─── Crispy Forms ─────────────────────────────────────────────────────────────
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'


# ─── Прочее ───────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# UUID для PK задаём не через DEFAULT_AUTO_FIELD (он не поддерживает UUID),
# а через базовую абстрактную модель — см. apps/core/models.py

# Максимальный размер загружаемого файла — 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800


# Для notifications
CELERY_BEAT_SCHEDULE = {
    # Каждый день в 9:00 по московскому времени
    'send-overdue-tasks-daily': {
        'task': 'notifications.send_overdue_tasks_notifications',
        'schedule': crontab(hour=9, minute=0),
    },
}

# ── django-allauth: OAuth вход через соцсети (только для клиентов) ────────
SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'APP': {
            'client_id': env('GITHUB_CLIENT_ID', default=''),
            'secret': env('GITHUB_CLIENT_SECRET', default=''),
            'key': '',
        },
        'SCOPE': ['user:email'],
    },
    'vk': {
        'APP': {
            'client_id': env('VK_CLIENT_ID', default=''),
            'secret': env('VK_CLIENT_SECRET', default=''),
            'key': '',
        },
    },
}


VK_OAUTH_ENABLED = bool(env('VK_CLIENT_ID', default=''))

# Отключаем встроенные страницы allauth (логин/регистрация/подтверждение) —
# используем только сам OAuth-флоу, свои формы уже написаны
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_LOGIN_ON_GET = True  # сразу редиректит на провайдера, без промежуточной страницы allauth

ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*']

# Кастомный adapter — создаёт клиента с правильной ролью и логикой
SOCIALACCOUNT_ADAPTER = 'apps.accounts.adapters.CustomSocialAccountAdapter' 

