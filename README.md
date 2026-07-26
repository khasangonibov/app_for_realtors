# CRM для агентства недвижимости

Полнофункциональная CRM-система на Django для агентств недвижимости — с публичным каталогом объектов, личным кабинетом клиента, внутренними чатами и REST API.

## Стек технологий

- **Backend:** Django 5.1, Python 3.13
- **База данных:** PostgreSQL
- **Кэш и очереди:** Redis, Celery
- **Хранилище файлов:** MinIO (S3-совместимое)
- **Frontend:** Django Templates, Bootstrap 5, HTMX, Select2, Leaflet, Chart.js (все библиотеки подключены локально, без CDN)
- **API:** Django REST Framework + JWT

## Структура проекта

apps/
├── core/ — базовые модели (UUIDModel, TimeStampedModel), management-команды
├── accounts/ — пользователи, агентства, роли, авторизация
├── properties/ — объекты недвижимости, публичный каталог, CRM
├── contacts/ — клиенты и лиды, история активностей
├── deals/ — сделки, kanban-доска
├── selections/ — подборки объектов для клиентов
├── tasks/ — задачи и напоминания
├── analytics/ — аналитика и графики
├── notifications/ — email-уведомления через Celery
└── chat/ — чаты (клиент↔риелтор, внутренние чаты сотрудников)

config/ — настройки проекта (base/development/production)
templates/ — HTML-шаблоны (CRM и публичная часть раздельно)
static/vendor/ — локально подключённые библиотеки фронтенда


## Роли пользователей

| Роль | Доступ |
|---|---|
| **Admin** | Полный доступ к CRM и настройкам агентства |
| **Manager** | Все объекты/контакты/сделки агентства, аналитика, управление сотрудниками |
| **Agent** | Только свои объекты, контакты, сделки, задачи |
| **Client** | Личный кабинет: подборки, чат с риелтором, публичный каталог |

## Быстрый старт (разработка)

### 1. Клонирование и окружение

```bash
git clone <repo_url>
cd <project_folder>
cp .env.example .env   # заполнить переменные окружения
```

### 2. Инфраструктура через Docker

```bash
docker compose up db redis minio -d
```

### 3. Виртуальное окружение и зависимости

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements/development.txt
```

### 4. Миграции и суперпользователь

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Тестовые данные (опционально)

```bash
python manage.py seed_data --count 20        # с фото (медленнее)
python manage.py seed_data --count 20 --no-photos   # без фото (быстро)
python manage.py seed_data --count 20 --clear        # очистить и создать заново
```

### 6. Запуск сервера

```bash
python manage.py runserver
```

CRM: `http://127.0.0.1:8000/crm/`
Публичный сайт: `http://127.0.0.1:8000/`
Django Admin: `http://127.0.0.1:8000/admin/`

## Основные разделы

### CRM (`/crm/`)
- Дашборд с календарём задач, мини-канбаном сделок, статистикой просмотров
- Объекты — список с фильтрами, пагинация, форма с загрузкой фото и характеристиками, геокодинг адреса
- Контакты — карточки с историей активностей
- Сделки — kanban-доска по стадиям
- Подборки — создание и отправка клиентам по публичной ссылке
- Задачи — с приоритетами и просроченными
- Аналитика — графики по объектам, контактам, сделкам, риелторам
- Чаты — с клиентами и внутренние (личные/групповые), с ответами на сообщения и статусами прочтения
- Сотрудники — приглашение, роли, деактивация

### Публичная часть (`/`)
- Каталог всех опубликованных объектов с фильтрами
- Карточка объекта — галерея, карта (Leaflet), контакты риелтора
- Сравнение объектов (до 4 штук, хранится в сессии)
- Регистрация и личный кабинет клиента
- Просмотр подборок и чат с риелтором

### REST API (`/api/v1/`)
JWT-авторизация, endpoints для объектов, контактов, сделок, задач, подборок.

```bash
# Получить токен
POST /api/v1/auth/token/
{"username": "...", "password": "..."}

# Использовать
GET /api/v1/properties/
Authorization: Bearer <token>
```

## Тестовые аккаунты (после `seed_data`)

| Логин | Пароль | Роль |
|---|---|---|
| `manager` | `testpass123` | Руководитель |
| `agent1` / `agent2` / `agent3` | `testpass123` | Риелтор |

## Переменные окружения

См. `.env.example` — основные:
DJANGO_SECRET_KEY=
DATABASE_URL=postgres://user:pass@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
USE_S3=False
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

## Деплой

Docker-образ уже настроен (`Dockerfile`, `docker-compose.yml`). На production сервере:

```bash
docker compose up -d
```

Подробности переноса на новый сервер — см. раздел «Перенос проекта» ниже.

### Перенос проекта на другой компьютер

```bash
git clone <repo_url>
cd <project_folder>
cp .env.example .env    # заполнить

docker compose up db redis minio -d

python -m venv venv
venv\Scripts\activate
pip install -r requirements/development.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Файлы, которые не хранятся в git и требуют переноса вручную:
- `.env` — секреты
- `media/` — загруженные фото объектов (или настроить S3/MinIO)
- База данных — через `pg_dump` / `psql`

## Известные особенности

- Polling чатов работает через HTMX (`every 5s`), без WebSocket — простое и надёжное решение без Django Channels
- Геокодинг адресов — через бесплатный Nominatim (OpenStreetMap), без API-ключей
- Все статические библиотеки (Bootstrap, HTMX, Leaflet, Select2, Chart.js) подключены локально — работа без интернета в разработке