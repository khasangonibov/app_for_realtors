# Промпт: Разработка CRM-системы для агентства недвижимости на Django

## Общее описание задачи

Разработай полноценную CRM-систему для агентств недвижимости и риелторов на Django (Python). Система должна включать публичную часть (карточки объектов, доступные по ссылке без авторизации) и закрытую CRM-часть (для риелторов и руководителей агентства). Аналог — платформа Topnlab.ru.

---

## Технический стек

- **Backend:** Python 3.12+, Django 5.x, Django REST Framework
- **База данных:** PostgreSQL
- **Очереди задач:** Celery + Redis
- **Хранение файлов:** S3-совместимое хранилище (MinIO или AWS S3) для фото и документов
- **Фронтенд CRM:** Django Templates + HTMX + Alpine.js (либо отдельный React SPA через DRF)
- **Публичные страницы объектов:** Django Templates + Bootstrap 5 (SSR для SEO)
- **Кэширование:** Redis
- **Поиск:** Django Q или PostgreSQL Full-Text Search (опционально — Elasticsearch)
- **Деплой:** Docker + docker-compose

---

## Роли пользователей

Реализуй систему ролей:

1. **Администратор** — полный доступ, управление агентством, тарифами, пользователями
2. **Руководитель** — доступ к аналитике, отчётам, всем объектам и сделкам агентства
3. **Риелтор** — работа со своими объектами, клиентами, сделками
4. **Клиент (внешний пользователь)** — просмотр публичных карточек объектов по ссылке (без авторизации или с ограниченной)

Используй Django Groups + кастомные пермишены для разграничения доступа.

---

## Модели данных (Models)

### 1. Пользователи и агентство

```python
# Agency — агентство недвижимости
- name, logo, city, description
- subscription_plan (choices: basic, standard, pro, enterprise)
- trial_expires_at, subscription_expires_at

# UserProfile (OneToOne к User)
- agency (FK → Agency)
- role (choices: admin, manager, agent, client)
- phone, avatar, bio
- is_active_agent
```

### 2. Объекты недвижимости (Property)

```python
# Property — основная карточка объекта
- agency (FK)
- agent (FK → User)
- deal_type (choices: sale, rent)
- property_type (choices: apartment, house, commercial, land, garage, room)
- title, description (RichTextField)
- price, price_currency (default RUB)
- price_per_sqm (вычисляемое поле)
- area_total, area_living, area_kitchen (FloatField, м²)
- floor, floors_total
- rooms_count
- address (CharField)
- city, district, street, building, apartment
- latitude, longitude (для карты)
- status (choices: active, reserved, sold, archived, draft)
- is_exclusive (эксклюзивный объект)
- is_published (опубликован в публичной части)
- public_token (UUID, уникальный токен для публичной ссылки)
- commission_percent, commission_fixed
- created_at, updated_at

# PropertyPhoto
- property (FK)
- image (ImageField → S3)
- is_cover (bool)
- order (IntegerField)

# PropertyDocument
- property (FK)
- file (FileField → S3)
- doc_type (choices: contract, passport, plan, other)
- name

# PropertyFeature (доп. характеристики)
- property (FK)
- key (например: "лифт", "балкон", "парковка")
- value

# PropertyView (статистика просмотров)
- property (FK)
- ip_address, user_agent
- viewed_at
```

### 3. Клиенты

```python
# Contact — клиент/лид
- agency (FK)
- agent (FK → User, ответственный)
- first_name, last_name, middle_name
- phone, email
- contact_type (choices: buyer, seller, tenant, landlord)
- source (choices: call, site, referral, avito, cian, other)
- status (choices: new, in_progress, done, rejected)
- budget_min, budget_max
- notes (TextField)
- created_at, updated_at

# ContactActivity — история взаимодействий
- contact (FK)
- agent (FK → User)
- activity_type (choices: call, meeting, email, note, task)
- description
- scheduled_at, completed_at
- is_done (bool)
```

### 4. Сделки

```python
# Deal — сделка
- agency (FK)
- property (FK → Property)
- seller_contact (FK → Contact)
- buyer_contact (FK → Contact)
- agent_seller (FK → User)
- agent_buyer (FK → User)
- deal_type (sale / rent)
- stage (choices: negotiation, deposit, documents, registration, closed, cancelled)
- price_agreed (согласованная цена)
- commission_total, commission_agent_share
- deposit_amount, deposit_date
- contract_date, close_date
- notes
- created_at, updated_at

# DealDocument
- deal (FK)
- file (FileField → S3)
- doc_type
- uploaded_by (FK → User)
```

### 5. Подборки для клиентов

```python
# Selection — подборка объектов под клиента
- contact (FK → Contact)
- agent (FK → User)
- title
- public_token (UUID для публичной ссылки)
- created_at

# SelectionItem
- selection (FK)
- property (FK)
- agent_comment
- client_status (choices: new, liked, rejected, maybe)
```

---

## Публичная карточка объекта

**URL:** `/object/{agency_slug}/{property_id}/{public_token}/`

Страница должна быть доступна без авторизации по ссылке (как в Topnlab). Реализуй:

### Отображаемая информация:
- Фотогалерея (слайдер, fullscreen-режим)
- Заголовок: тип сделки | тип объекта | площадь | этаж/этажей | цена
- Адрес объекта
- Описание (полный текст)
- Блок характеристик (таблица): площадь, комнаты, этаж, тип дома, год постройки, санузел, балкон, лифт и др.
- Контакт агента (имя, фото, телефон — кнопка «Позвонить», кнопка «Написать в WhatsApp/Telegram»)
- Карта (Яндекс.Карты или Leaflet) с маркером объекта
- OG-теги для красивого превью при шаринге в мессенджерах (title, description, image)
- Счётчик просмотров (фиксировать уникальные просмотры по IP)

### SEO мета-теги (как у оригинала):
```html
<meta name="description" content="{адрес} — {краткое описание}">
<meta property="og:title" content="{тип сделки} | {тип объекта} | {площадь} | {этаж} | {цена}">
<meta property="og:image" content="{обложка}">
<meta name="referrer" content="no-referrer">
```

---

## CRM-интерфейс (закрытая часть)

### Дашборд (`/crm/`)
- Виджеты: мои объекты, активные сделки, задачи на сегодня, новые лиды
- График активности за последние 30 дней
- Быстрые действия: добавить объект, добавить контакт, создать подборку

### Объекты (`/crm/properties/`)
- Список объектов с фильтрами: тип, статус, город, район, цена, площадь, комнаты
- Переключение вид: карточки / список / карта
- Быстрое добавление/редактирование объекта
- Массовые действия: архивировать, опубликовать, экспорт в Excel
- Кнопка «Скопировать ссылку» для публичной карточки
- Кнопка «Поделиться» — генерация QR-кода ссылки

### Карточка объекта в CRM (`/crm/properties/{id}/`)
- Полная форма редактирования объекта
- Загрузка и сортировка фотографий (drag&drop)
- Загрузка документов
- Вкладка «История» — все действия по объекту
- Вкладка «Сделки» — связанные сделки
- Кнопка «Создать подборку» с этим объектом

### Контакты (`/crm/contacts/`)
- Список с фильтрами: тип, статус, источник, ответственный агент
- Карточка контакта: данные, история взаимодействий, задачи, подборки
- Лента активности (таймлайн звонков, встреч, заметок)
- Форма добавления активности

### Сделки (`/crm/deals/`)
- Kanban-доска по стадиям сделки (drag&drop между стадиями)
- Список сделок с фильтрами
- Карточка сделки: участники, документы, хронология
- Расчёт комиссии агента

### Подборки (`/crm/selections/`)
- Создание подборки: выбрать клиента → добавить объекты → отправить ссылку
- Публичная страница подборки (аналогично карточке объекта)
- Просмотр реакций клиента на объекты в подборке

### Задачи (`/crm/tasks/`)
- Список задач с приоритетами и сроками
- Связь задачи с контактом/объектом/сделкой
- Уведомления о просроченных задачах (email + in-app)

---

## REST API (Django REST Framework)

Реализуй API для работы с мобильным клиентом и внешними интеграциями:

```
GET/POST   /api/v1/properties/
GET/PUT    /api/v1/properties/{id}/
GET        /api/v1/properties/{id}/public/   # публичные данные без авторизации
POST       /api/v1/properties/{id}/photos/
DELETE     /api/v1/properties/{id}/photos/{photo_id}/

GET/POST   /api/v1/contacts/
GET/PUT    /api/v1/contacts/{id}/
POST       /api/v1/contacts/{id}/activities/

GET/POST   /api/v1/deals/
GET/PUT    /api/v1/deals/{id}/

GET/POST   /api/v1/selections/
GET        /api/v1/selections/{token}/public/

GET        /api/v1/analytics/dashboard/
GET        /api/v1/analytics/properties/
GET        /api/v1/analytics/deals/
```

Аутентификация: JWT (djangorestframework-simplejwt).

---

## Уведомления и автоматизация

- **Email-уведомления** (через Celery): новый лид, просроченная задача, изменение стадии сделки
- **Напоминания**: автоматическая задача «перезвонить через N дней» при переходе статуса контакта
- **Счётчик просмотров**: фиксация через middleware или API endpoint, агрегация статистики

---

## Аналитика (для руководителя)

- Количество объектов по статусам
- Конверсия лидов в сделки
- Средний цикл сделки в днях
- Доходность по агентам (кол-во сделок, комиссия)
- Источники лидов (откуда приходят клиенты)
- Просмотры публичных карточек

Используй Django ORM (annotate/aggregate) для отчётов. Вывод через Chart.js или Recharts.

---

## Структура Django-проекта

```
project/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── celery.py
├── apps/
│   ├── accounts/        # Пользователи, агентства, роли
│   ├── properties/      # Объекты, фото, характеристики
│   ├── contacts/        # Клиенты, активности
│   ├── deals/           # Сделки, документы
│   ├── selections/      # Подборки
│   ├── tasks/           # Задачи, напоминания
│   ├── analytics/       # Отчёты, дашборд
│   └── notifications/   # Email и in-app уведомления
├── templates/
│   ├── public/          # Публичные страницы объектов
│   └── crm/             # CRM-интерфейс
├── static/
├── media/
├── docker-compose.yml
└── requirements/
    ├── base.txt
    ├── development.txt
    └── production.txt
```

---

## Безопасность

- Публичная ссылка на объект содержит UUID-токен — без токена объект недоступен
- Все CRM-страницы защищены `@login_required` + проверка принадлежности к агентству
- Для API — JWT + проверка `agency` на уровне сериализаторов
- Защита от CSRF, XSS (экранирование в шаблонах)
- Rate limiting на публичных endpoints (django-ratelimit)

---

## Требования к реализации

1. Начни с настройки проекта: `django-admin startproject config .`, создай все приложения через `manage.py startapp`
2. Настрой PostgreSQL через `dj-database-url`
3. Реализуй модели в порядке зависимостей: accounts → properties → contacts → deals → selections
4. Создай миграции и базовые fixtures (тестовые данные)
5. Реализуй публичную карточку объекта (приоритет #1 — именно она видна клиентам)
6. Реализуй базовый CRM-интерфейс для риелтора
7. Подключи S3 через `django-storages` + `boto3`
8. Напиши тесты (pytest-django) для критичных endpoint'ов

---

## Дополнительные пожелания

- Интерфейс на русском языке (`LANGUAGE_CODE = 'ru-ru'`)
- Временная зона: `TIME_ZONE = 'Europe/Moscow'` (с поддержкой смены для регионов)
- Адаптивный дизайн (mobile-first) для публичных страниц
- Поддержка мультиагентства: данные агентства изолированы (каждое агентство видит только свои данные)
