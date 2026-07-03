"""
Management command для заполнения БД тестовыми данными.

Запуск:
    python manage.py seed_data

Опции:
    --clear     Удалить все данные перед созданием новых
    --count     Количество объектов (по умолчанию 20)
"""

import random
import urllib.request
import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.files import File
from django.utils import timezone
from datetime import timedelta
import tempfile

from apps.accounts.models import Agency, User, UserProfile
from apps.properties.models import Property, PropertyPhoto, PropertyFeature
from apps.contacts.models import Contact, ContactActivity
from apps.deals.models import Deal
from apps.tasks.models import Task


# ── Данные для генерации ──────────────────────────────────────────────────────

CITIES = [
    'Москва', 'Санкт-Петербург', 'Казань', 'Нальчик',
    'Краснодар', 'Сочи', 'Ростов-на-Дону', 'Екатеринбург',
]

STREETS = [
    'ул. Ленина', 'пр. Мира', 'ул. Пушкина', 'ул. Гагарина',
    'пр. Победы', 'ул. Садовая', 'ул. Центральная', 'пр. Кирова',
    'ул. Советская', 'ул. Строителей', 'бул. Цветочный',
]

DISTRICTS = [
    'Центральный', 'Северный', 'Южный', 'Западный',
    'Восточный', 'Новый', 'Старый город',
]

FIRST_NAMES = [
    'Александр', 'Мария', 'Дмитрий', 'Анна', 'Сергей',
    'Елена', 'Иван', 'Ольга', 'Андрей', 'Наталья',
    'Хасан', 'Фатима', 'Заур', 'Лейла', 'Руслан',
]

LAST_NAMES = [
    'Иванов', 'Петров', 'Сидоров', 'Кузнецов', 'Попов',
    'Новиков', 'Морозов', 'Волков', 'Гончаров', 'Соколов',
    'Гонибов', 'Кабардов', 'Тлупов', 'Шогенов', 'Беров',
]

PROPERTY_DESCRIPTIONS = [
    'Просторная квартира в тихом районе с развитой инфраструктурой. '
    'Рядом школы, детские сады, магазины. Отличное состояние.',

    'Уютная квартира с красивым видом на город. Свежий ремонт, '
    'встроенная кухня, новая сантехника. Готова к заселению.',

    'Квартира в новом доме с закрытой территорией. Подземный паркинг, '
    'охрана, консьерж. Тихий двор, детская площадка.',

    'Светлая квартира на высоком этаже. Панорамные окна, '
    'просторные комнаты. Дом расположен в зелёном квартале.',

    'Отличный вариант для семьи. Большая кухня-гостиная, '
    'две спальни, гардеробная. Развитая инфраструктура рядом.',
]

AGENT_FEATURES = [
    {'key': 'Тип дома', 'values': ['Панельный', 'Кирпичный', 'Монолитный', 'Блочный']},
    {'key': 'Санузел', 'values': ['Раздельный', 'Совмещённый', '2 санузла']},
    {'key': 'Балкон', 'values': ['Есть', 'Нет', 'Лоджия', '2 балкона']},
    {'key': 'Лифт', 'values': ['Есть', 'Нет', '2 лифта']},
    {'key': 'Парковка', 'values': ['Подземная', 'Наземная', 'Нет']},
    {'key': 'Отопление', 'values': ['Центральное', 'Индивидуальное', 'Газовое']},
    {'key': 'Ремонт', 'values': ['Евро', 'Косметический', 'Без ремонта', 'Дизайнерский']},
    {'key': 'Окна', 'values': ['Во двор', 'На улицу', 'На обе стороны']},
]


class Command(BaseCommand):
    help = 'Заполняет БД тестовыми данными'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить все данные перед созданием новых',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Количество объектов недвижимости (по умолчанию 20)',
        )
        parser.add_argument(
            '--no-photos',
            action='store_true',
            help='Не скачивать фото (быстрее)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Очищаем данные...')
            Task.objects.all().delete()
            Deal.objects.all().delete()
            Contact.objects.all().delete()
            Property.objects.all().delete()
            UserProfile.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            Agency.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Данные очищены.'))

        count = options['count']
        download_photos = not options['no_photos']

        # ── 1. Агентство ──────────────────────────────────────────────────
        self.stdout.write('Создаём агентство...')
        agency, _ = Agency.objects.get_or_create(
            slug='test-agency',
            defaults={
                'name': 'Тестовое агентство недвижимости',
                'city': 'Москва',
                'phone': '+7 (495) 123-45-67',
                'email': 'info@test-agency.ru',
                'description': 'Профессиональное агентство недвижимости с многолетним опытом работы.',
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Агентство: {agency.name}'))

        # ── 2. Пользователи ───────────────────────────────────────────────
        self.stdout.write('Создаём пользователей...')
        users = []

        # Менеджер
        manager, created = User.objects.get_or_create(
            username='manager',
            defaults={
                'email': 'manager@test-agency.ru',
                'first_name': 'Алексей',
                'last_name': 'Менеджеров',
                'agency': agency,
                'phone': '+7 (900) 111-22-33',
                'is_staff': True,
            }
        )
        if created:
            manager.set_password('testpass123')
            manager.save()
        UserProfile.objects.get_or_create(
            user=manager,
            defaults={'role': UserProfile.Role.MANAGER}
        )
        users.append(manager)

        # Риелторы
        agent_data = [
            ('agent1', 'Иван', 'Риелторов', '+7 (900) 222-33-44'),
            ('agent2', 'Мария', 'Агентова', '+7 (900) 333-44-55'),
            ('agent3', 'Сергей', 'Продавцов', '+7 (900) 444-55-66'),
        ]
        agents = []
        for username, first, last, phone in agent_data:
            agent, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@test-agency.ru',
                    'first_name': first,
                    'last_name': last,
                    'agency': agency,
                    'phone': phone,
                }
            )
            if created:
                agent.set_password('testpass123')
                agent.save()
            UserProfile.objects.get_or_create(
                user=agent,
                defaults={'role': UserProfile.Role.AGENT}
            )
            agents.append(agent)
            users.append(agent)

        self.stdout.write(self.style.SUCCESS(f'Создано пользователей: {len(users)}'))
        self.stdout.write('Логины: manager, agent1, agent2, agent3')
        self.stdout.write('Пароль для всех: testpass123')

        # ── 3. Объекты недвижимости ───────────────────────────────────────
        self.stdout.write(f'Создаём {count} объектов...')
        properties = []

        property_types = [t[0] for t in Property.PropertyType.choices]
        deal_types = [t[0] for t in Property.DealType.choices]
        statuses = ['active', 'active', 'active', 'reserved', 'draft']

        for i in range(count):
            city = random.choice(CITIES)
            prop_type = random.choice(property_types)
            deal_type = random.choice(deal_types)
            rooms = random.randint(1, 5) if prop_type == 'apartment' else None
            area = round(random.uniform(30, 200), 1)
            floor = random.randint(1, 20)
            floors_total = random.randint(floor, 25)

            if deal_type == 'sale':
                price = Decimal(random.randint(3, 50)) * Decimal('1000000')
            else:
                price = Decimal(random.randint(20, 200)) * Decimal('1000')

            prop = Property.objects.create(
                agency=agency,
                agent=random.choice(agents),
                deal_type=deal_type,
                property_type=prop_type,
                status=random.choice(statuses),
                title='',
                description=random.choice(PROPERTY_DESCRIPTIONS),
                price=price,
                price_currency='RUB',
                area_total=Decimal(str(area)),
                area_living=Decimal(str(round(area * 0.6, 1))),
                area_kitchen=Decimal(str(round(area * 0.15, 1))),
                rooms_count=rooms,
                floor=floor,
                floors_total=floors_total,
                city=city,
                district=random.choice(DISTRICTS),
                street=random.choice(STREETS),
                building=str(random.randint(1, 120)),
                apartment=str(random.randint(1, 200)),
                latitude=Decimal(str(round(random.uniform(43.0, 56.0), 7))),
                longitude=Decimal(str(round(random.uniform(37.0, 50.0), 7))),
                is_published=random.choice([True, True, True, False]),
                is_exclusive=random.choice([True, False, False, False]),
                commission_percent=Decimal(str(random.choice([2, 3, 4, 5]))),
            )
            properties.append(prop)

            # Характеристики
            features_count = random.randint(3, len(AGENT_FEATURES))
            for feature_data in random.sample(AGENT_FEATURES, features_count):
                PropertyFeature.objects.create(
                    property=prop,
                    key=feature_data['key'],
                    value=random.choice(feature_data['values']),
                )

            # Фото
            if download_photos:
                self._download_photos(prop, random.randint(2, 5))

            if (i + 1) % 5 == 0:
                self.stdout.write(f'  Создано {i + 1}/{count} объектов...')

        self.stdout.write(self.style.SUCCESS(f'Объекты созданы: {len(properties)}'))

        # ── 4. Контакты ───────────────────────────────────────────────────
        self.stdout.write('Создаём контакты...')
        contacts = []
        contact_types = [t[0] for t in Contact.ContactType.choices]
        contact_statuses = [t[0] for t in Contact.Status.choices]
        sources = [t[0] for t in Contact.Source.choices]

        for i in range(count * 2):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            contact = Contact.objects.create(
                agency=agency,
                agent=random.choice(agents),
                first_name=first,
                last_name=last,
                phone=f'+7 (9{random.randint(10, 99)}) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
                email=f'{first.lower()}.{last.lower()}{random.randint(1, 99)}@mail.ru',
                contact_type=random.choice(contact_types),
                status=random.choice(contact_statuses),
                source=random.choice(sources),
                budget_min=Decimal(random.randint(2, 5)) * Decimal('1000000'),
                budget_max=Decimal(random.randint(6, 15)) * Decimal('1000000'),
                notes='Тестовый контакт. Интересуется недвижимостью.',
                created_at=timezone.now() - timedelta(days=random.randint(0, 60)),
            )
            contacts.append(contact)

            # Добавляем 1-3 активности
            for _ in range(random.randint(1, 3)):
                activity_types = [t[0] for t in ContactActivity.ActivityType.choices]
                ContactActivity.objects.create(
                    contact=contact,
                    agent=contact.agent,
                    activity_type=random.choice(activity_types),
                    description=random.choice([
                        'Позвонил, обсудили варианты.',
                        'Встретились в офисе, показали несколько объектов.',
                        'Отправил подборку объектов на email.',
                        'Клиент просит перезвонить после выходных.',
                        'Согласовали показ объекта на следующей неделе.',
                    ]),
                    created_at=timezone.now() - timedelta(days=random.randint(0, 30)),
                )

        self.stdout.write(self.style.SUCCESS(f'Контакты созданы: {len(contacts)}'))

        # ── 5. Сделки ─────────────────────────────────────────────────────
        self.stdout.write('Создаём сделки...')
        stages = [t[0] for t in Deal.Stage.choices]
        deals_count = max(5, count // 4)

        for i in range(deals_count):
            prop = random.choice(properties)
            buyer = random.choice(contacts)
            seller = random.choice(contacts)
            stage = random.choice(stages)
            close_date = None
            if stage == 'closed':
                close_date = (timezone.now() - timedelta(days=random.randint(1, 30))).date()

            Deal.objects.create(
                agency=agency,
                agent=random.choice(agents),
                property=prop,
                buyer_contact=buyer,
                seller_contact=seller,
                stage=stage,
                price_agreed=prop.price * Decimal('0.95'),
                commission_total=prop.price * Decimal('0.03'),
                deposit_amount=prop.price * Decimal('0.05'),
                deposit_date=(timezone.now() - timedelta(days=random.randint(5, 30))).date(),
                close_date=close_date,
                notes='Тестовая сделка.',
            )

        self.stdout.write(self.style.SUCCESS(f'Сделки созданы: {deals_count}'))

        # ── 6. Задачи ─────────────────────────────────────────────────────
        self.stdout.write('Создаём задачи...')
        task_types = [t[0] for t in Task.TaskType.choices]
        priorities = [t[0] for t in Task.Priority.choices]

        for agent in agents:
            for i in range(random.randint(3, 8)):
                due_days = random.randint(-5, 14)
                is_done = due_days < -2 and random.choice([True, False])
                Task.objects.create(
                    agency=agency,
                    agent=agent,
                    contact=random.choice(contacts) if random.choice([True, False]) else None,
                    title=random.choice([
                        'Позвонить клиенту',
                        'Показ объекта',
                        'Подготовить документы',
                        'Встреча с покупателем',
                        'Отправить подборку',
                        'Согласование договора',
                        'Регистрация в Росреестре',
                    ]),
                    task_type=random.choice(task_types),
                    priority=random.choice(priorities),
                    due_date=timezone.now() + timedelta(days=due_days),
                    is_done=is_done,
                    done_at=timezone.now() if is_done else None,
                )

        self.stdout.write(self.style.SUCCESS('Задачи созданы.'))

        # ── Итог ──────────────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'Агентство:  {agency.name}')
        self.stdout.write(f'Объектов:   {len(properties)}')
        self.stdout.write(f'Контактов:  {len(contacts)}')
        self.stdout.write(f'Сделок:     {deals_count}')
        self.stdout.write('')
        self.stdout.write('Логины для входа:')
        self.stdout.write('  manager  / testpass123  (руководитель)')
        self.stdout.write('  agent1   / testpass123  (риелтор)')
        self.stdout.write('  agent2   / testpass123  (риелтор)')
        self.stdout.write('  agent3   / testpass123  (риелтор)')

    def _download_photos(self, property_obj, count):
        """Скачивает случайные фото с picsum.photos и прикрепляет к объекту."""
        for i in range(count):
            try:
                # picsum.photos отдаёт случайную картинку по размеру
                width = random.choice([800, 1024, 1200])
                height = random.choice([600, 768, 800])
                seed = random.randint(1, 1000)
                url = f'https://picsum.photos/seed/{seed}/{width}/{height}'

                # Скачиваем во временный файл
                with tempfile.NamedTemporaryFile(
                    suffix='.jpg', delete=False
                ) as tmp:
                    urllib.request.urlretrieve(url, tmp.name)
                    tmp_path = tmp.name

                # Прикрепляем к объекту
                with open(tmp_path, 'rb') as f:
                    photo = PropertyPhoto(
                        property=property_obj,
                        is_cover=(i == 0),  # первое фото — обложка
                        order=i,
                    )
                    photo.image.save(
                        f'property_{property_obj.pk}_{i}.jpg',
                        File(f),
                        save=True,
                    )

                os.unlink(tmp_path)  # удаляем временный файл

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Не удалось скачать фото: {e}')
                )