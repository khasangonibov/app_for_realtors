"""
Management command для заполнения БД тестовыми данными.

Запуск:
    python manage.py seed_data

Опции:
    --clear     Удалить все данные перед созданием новых
    --count     Количество объектов (по умолчанию 20)
"""

"""Django management command: realistic CRM demo data.
Creates 50 properties, 100 contacts, 30 deals and 10 tasks per seed user.
Coordinates are intentionally left empty; CRM geocodes the full address.
"""
import os, random, tempfile, urllib.request
from decimal import Decimal
from datetime import timedelta
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import Agency, User, UserProfile
from apps.properties.models import Property, PropertyPhoto, PropertyFeature
from apps.contacts.models import Contact, ContactActivity
from apps.deals.models import Deal
from apps.tasks.models import Task

SEED=20260814
NAMES=['Александр','Мария','Дмитрий','Анна','Сергей','Елена','Иван','Ольга','Андрей','Наталья','Михаил','Екатерина','Максим','Виктория','Артём','Полина','Роман','Дарья','Никита','София','Хасан','Фатима','Заур','Лейла','Руслан']
LAST=['Иванов','Петров','Сидоров','Кузнецов','Попов','Новиков','Морозов','Волков','Гончаров','Соколов','Гонибов','Кабардов','Тлупов','Шогенов','Беров','Орлов','Фёдоров','Алексеев','Власов','Захаров']
ACT=['Позвонил, обсудили подходящие варианты.','Встретились в офисе, уточнили требования клиента.','Отправил подборку объектов на email.','Клиент попросил добавить варианты в другом районе.','Согласовали показ объекта на следующей неделе.','Клиент сравнивает несколько предложений.','Уточнил бюджет и желаемую площадь.','Клиент готов рассмотреть альтернативный вариант.']
NOTES=['Ищет квартиру для собственного проживания.','Интересуется новостройками.','Готов к покупке после просмотра нескольких объектов.','Просит подобрать варианты в указанном бюджете.','Рассматривает покупку в течение ближайших двух месяцев.','Интересуется объектами с хорошим ремонтом и парковкой.','Ищет вариант для семьи.','Рассматривает инвестиционный объект под аренду.']
TASKS=['Позвонить клиенту','Показ объекта','Подготовить документы','Встреча с покупателем','Отправить подборку','Согласование договора','Проверить документы объекта','Уточнить условия сделки','Подготовить объект к показу','Перезвонить продавцу']

# 50 coherent cards. Format: city,district,street,building,apt,type,deal,rooms,area,living,kitchen,floor,total,price,title,description,features,tags
RAW = [('Москва', 'Хорошёвский', 'Хорошёвское шоссе', '38А', '124', 'apartment', 'sale', 3, 78.4, 46.2, 13.8, 12, 24, 21500000, 'Просторная 3-комнатная квартира в Хорошёвском районе', 'Светлая семейная квартира в современном доме. Большая кухня-гостиная, две спальни, лоджия и два санузла. Рядом метро, школы, магазины и парк.', 'Монолитный|2 санузла|Лоджия|2 лифта|Подземная|Евро|На обе стороны', 'modern apartment kitchen living room bedroom bathroom'), ('Москва', 'Пресненский', 'Большая Грузинская улица', '69', '57', 'apartment', 'sale', 2, 61.7, 34.5, 12.4, 7, 10, 24900000, 'Двухкомнатная квартира рядом с центром Москвы', 'Уютная квартира с современным ремонтом, встроенной техникой и большими окнами. Спокойный двор, метро и городская инфраструктура рядом.', 'Кирпичный|Совмещённый|Есть|Есть|Наземная|Дизайнерский|Во двор', 'moscow apartment modern kitchen living room bedroom bathroom'), ('Москва', 'Раменки', 'Мичуринский проспект', '29', '211', 'apartment', 'sale', 1, 42.3, 21, 11.2, 15, 25, 13900000, 'Светлая однокомнатная квартира в Раменках', 'Функциональная квартира в новом доме с закрытой территорией. Просторная комната, кухня с лоджией и гардеробная. Рядом парк и университеты.', 'Монолитный|Совмещённый|Лоджия|2 лифта|Подземная|Евро|На улицу', 'modern one bedroom apartment kitchen bedroom balcony bathroom'), ('Москва', 'Марьино', 'Люблинская улица', '161', '83', 'apartment', 'sale', 2, 55.8, 31.7, 10.4, 9, 17, 12600000, 'Уютная 2-комнатная квартира у метро', 'Квартира с аккуратным ремонтом, изолированными комнатами, просторной кухней и застеклённым балконом. Рядом школа, сад и метро.', 'Панельный|Раздельный|Есть|2 лифта|Наземная|Косметический|Во двор', 'russian apartment kitchen living room bedroom bathroom'), ('Москва', 'Тропарёво-Никулино', 'улица Академика Анохина', '9', '318', 'apartment', 'sale', 4, 104.6, 61.3, 17.5, 18, 22, 32500000, 'Четырёхкомнатная квартира для большой семьи', 'Большая кухня-гостиная, три спальни, гардеробная, два санузла и две лоджии. Панорамные окна, закрытый двор и подземный паркинг.', 'Монолитно-кирпичный|2 санузла|2 балкона|2 лифта|Подземная|Дизайнерский|На обе стороны', 'luxury family apartment kitchen living room bedrooms bathroom'), ('Москва', 'Соколиная Гора', 'улица Бориса Жигулёнкова', '27', '46', 'apartment', 'rent', 1, 37.6, 18.9, 9.8, 6, 16, 75000, 'Однокомнатная квартира в аренду', 'Полностью меблированная квартира после ремонта. Техника, кондиционер и застеклённая лоджия. Удобный выезд в центр.', 'Монолитный|Совмещённый|Лоджия|2 лифта|Наземная|Евро|Во двор', 'modern rental apartment furnished kitchen bedroom bathroom'), ('Москва', 'Кунцево', 'улица Ярцевская', '24', '96', 'apartment', 'sale', 3, 83.2, 48.1, 14.6, 11, 17, 23900000, 'Трёхкомнатная квартира с видом на зелёный район', 'Тихая квартира рядом с парком. Просторная кухня, изолированные комнаты, два санузла и лоджия. Окна на две стороны.', 'Монолитный|2 санузла|Лоджия|2 лифта|Подземная|Евро|На обе стороны', 'bright apartment green view kitchen living room bedroom bathroom'), ('Москва', 'Мещанский', 'улица Щепкина', '64', '32', 'apartment', 'sale', 2, 58.1, 33.4, 11.7, 4, 8, 22700000, 'Двухкомнатная квартира в тихом центре', 'Кирпичный дом недалеко от центра. Высокие потолки, большие окна, изолированные комнаты.', 'Кирпичный|Раздельный|Есть|Есть|Наземная|Косметический|Во двор', 'moscow classic apartment kitchen bedroom living room'), ('Санкт-Петербург', 'Петроградский', 'Каменноостровский проспект', '42', '19', 'apartment', 'sale', 3, 92.5, 55, 15.2, 5, 7, 28900000, 'Трёхкомнатная квартира на Петроградской стороне', 'Квартира с высокими потолками и дизайнерским ремонтом. Кухня-гостиная, две спальни и закрытый двор.', 'Кирпичный|2 санузла|Нет|Есть|Наземная|Дизайнерский|На улицу', 'saint petersburg apartment classic kitchen living room bedroom'), ('Санкт-Петербург', 'Приморский', 'Комендантский проспект', '58', '217', 'apartment', 'sale', 2, 59.4, 33.1, 12, 13, 25, 11900000, 'Двухкомнатная квартира в новом жилом комплексе', 'Современная квартира с панорамными окнами и большой лоджией. Закрытая территория, детская площадка и паркинг.', 'Монолитный|Совмещённый|Лоджия|2 лифта|Подземная|Евро|На улицу', 'modern saint petersburg apartment kitchen living room bedroom balcony'), ('Санкт-Петербург', 'Московский', 'Московский проспект', '183', '74', 'apartment', 'sale', 1, 39.8, 19.4, 10.1, 8, 12, 9200000, 'Однокомнатная квартира у Московского проспекта', 'Светлая квартира с современным ремонтом, гардеробной и встроенной техникой. Рядом метро и парки.', 'Кирпичный|Совмещённый|Есть|Есть|Наземная|Евро|Во двор', 'modern one bedroom apartment kitchen bedroom bathroom'), ('Санкт-Петербург', 'Василеостровский', 'Средний проспект В.О.', '87', '41', 'apartment', 'sale', 2, 64.2, 36.5, 12.8, 3, 6, 14700000, 'Двухкомнатная квартира на Васильевском острове', 'Кирпичный дом с высокими потолками. Ремонт, изолированные комнаты и застеклённый балкон.', 'Кирпичный|Раздельный|Есть|Есть|Наземная|Евро|Во двор', 'saint petersburg classic apartment kitchen bedroom living room balcony'), ('Санкт-Петербург', 'Выборгский', 'улица Есенина', '12', '154', 'apartment', 'rent', 2, 54.7, 31, 9.5, 10, 16, 55000, 'Уютная двухкомнатная квартира в аренду', 'Меблированная квартира с техникой, застеклённым балконом и тихим двором. Рядом метро.', 'Панельный|Раздельный|Есть|2 лифта|Наземная|Косметический|Во двор', 'rental apartment furnished kitchen living room bedroom'), ('Казань', 'Вахитовский', 'улица Татарстан', '18', '46', 'apartment', 'sale', 2, 63.5, 35.8, 13.2, 6, 10, 11800000, 'Двухкомнатная квартира в центре Казани', 'Современный ремонт, просторная кухня, изолированные комнаты и лоджия. Рядом набережная, школы и кафе.', 'Монолитно-кирпичный|Совмещённый|Лоджия|Есть|Наземная|Евро|На обе стороны', 'kazan modern apartment kitchen living room bedroom bathroom'), ('Казань', 'Советский', 'улица Аделя Кутуя', '110', '203', 'apartment', 'sale', 3, 82.1, 47, 14, 14, 18, 12900000, 'Семейная трёхкомнатная квартира в новом доме', 'Кухня-гостиная, две спальни, гардеробная, закрытый двор и подземный паркинг.', 'Монолитный|2 санузла|Лоджия|2 лифта|Подземная|Евро|На обе стороны', 'modern family apartment kitchen living room bedrooms bathroom'), ('Казань', 'Ново-Савиновский', 'проспект Ямашева', '103', '78', 'apartment', 'sale', 1, 38.9, 18, 10.5, 9, 16, 6900000, 'Однокомнатная квартира рядом с парком', 'Компактная квартира с хорошим ремонтом, кухней с техникой и лоджией.', 'Монолитный|Совмещённый|Лоджия|2 лифта|Наземная|Евро|Во двор', 'modern one bedroom apartment kitchen bedroom balcony'), ('Казань', 'Приволжский', 'улица Рихарда Зорге', '75', '121', 'apartment', 'sale', 2, 57.3, 32.4, 11.1, 7, 14, 7850000, 'Светлая 2-комнатная квартира после ремонта', 'Изолированные комнаты, кухня с балконом, раздельный санузел. Рядом школы и магазины.', 'Панельный|Раздельный|Есть|2 лифта|Наземная|Евро|Во двор', 'bright apartment kitchen living room bedroom bathroom balcony'), ('Сочи', 'Центральный', 'улица Войкова', '31', '54', 'apartment', 'sale', 2, 61.4, 34.2, 12, 8, 14, 18900000, 'Двухкомнатная квартира с видом на море', 'Современная квартира в центре Сочи. Панорамный вид, большая лоджия, кухня-гостиная и спальня. До набережной пешком.', 'Монолитный|2 санузла|Лоджия|2 лифта|Подземная|Дизайнерский|На улицу', 'sochi sea view luxury apartment kitchen living room bedroom balcony'), ('Сочи', 'Хостинский', 'Курортный проспект', '105', '37', 'apartment', 'sale', 1, 39.2, 19, 10.7, 5, 12, 12100000, 'Квартира для отдыха рядом с морем', 'Светлая квартира с большой лоджией и видом на зелёный склон. Мебель и техника остаются.', 'Монолитный|Совмещённый|Лоджия|Есть|Наземная|Евро|На улицу', 'sochi apartment sea balcony modern interior kitchen bedroom'), ('Сочи', 'Адлерский', 'улица Ленина', '219', '86', 'apartment', 'rent', 2, 58.6, 32, 11.5, 10, 16, 95000, 'Двухкомнатная квартира у моря в Адлере', 'Меблированная квартира с панорамными окнами, кондиционером и техникой.', 'Монолитный|Совмещённый|Есть|2 лифта|Подземная|Евро|На улицу', 'sochi adler modern rental apartment kitchen bedroom balcony'), ('Сочи', 'Лазаревский', 'улица Победы', '76', '14', 'apartment', 'sale', 3, 79.8, 44.5, 14, 4, 9, 15400000, 'Трёхкомнатная квартира с большой террасой', 'Кухня-гостиная, две спальни, большая терраса, закрытая территория и парковка.', 'Монолитный|2 санузла|2 балкона|Есть|Наземная|Евро|На обе стороны', 'sochi apartment terrace sea view living room kitchen bedroom'), ('Краснодар', 'Центральный', 'улица Красная', '176', '92', 'apartment', 'sale', 3, 76.5, 43.8, 13.4, 8, 16, 10400000, 'Трёхкомнатная квартира в центре Краснодара', 'Кухня-гостиная, две спальни, лоджия и два санузла. Рядом школы, магазины и парк.', 'Монолитный|2 санузла|Лоджия|2 лифта|Подземная|Евро|На обе стороны', 'krasnodar modern apartment kitchen living room bedrooms bathroom'), ('Краснодар', 'Фестивальный', 'улица Тургенева', '145', '61', 'apartment', 'sale', 2, 62.8, 35.4, 12.6, 6, 12, 8600000, 'Двухкомнатная квартира в Фестивальном районе', 'Хороший ремонт, две изолированные комнаты, гардеробная и лоджия.', 'Монолитно-кирпичный|Раздельный|Лоджия|Есть|Наземная|Евро|Во двор', 'krasnodar apartment interior kitchen living room bedroom balcony'), ('Краснодар', 'Юбилейный', 'проспект Чекистов', '39', '177', 'apartment', 'sale', 1, 41.7, 20.5, 11.3, 11, 16, 6250000, 'Однокомнатная квартира с ремонтом', 'Светлая квартира в новом доме. Кухня с техникой, лоджия. Рядом набережная, школа и детский сад.', 'Монолитный|Совмещённый|Лоджия|2 лифта|Наземная|Евро|На улицу', 'krasnodar one bedroom apartment modern kitchen bedroom bathroom'), ('Краснодар', 'Прикубанский', 'улица Московская', '142', '303', 'apartment', 'rent', 2, 55.2, 30, 10.8, 9, 17, 48000, 'Двухкомнатная квартира в аренду', 'Меблированная квартира в новом доме. Техника, кондиционер, лоджия и закрытая территория.', 'Монолитный|Совмещённый|Лоджия|2 лифта|Наземная|Евро|Во двор', 'krasnodar furnished rental apartment kitchen bedroom living room'), 
       ('Ростов-на-Дону', 'Кировский', 'Большая Садовая улица', '98', '44', 'apartment', 'sale', 2, 59.8, 33.2, 12.3, 5, 9, 7900000, 'Двухкомнатная квартира на Большой Садовой', 'Кирпичный дом, высокие потолки, современный ремонт, изолированные комнаты и балкон.', 'Кирпичный|Раздельный|Есть|Есть|Наземная|Евро|На улицу', 'rostov apartment classic modern kitchen living room bedroom'), ('Ростов-на-Дону', 'Ленинский', 'улица Станиславского', '52', '18', 'apartment', 'sale', 3, 84.3, 49, 14.8, 7, 12, 11300000, 'Большая 3-комнатная квартира в центре', 'Кухня-гостиная, две спальни, гардеробная, два санузла и лоджия.', 'Монолитно-кирпичный|2 санузла|Лоджия|2 лифта|Подземная|Евро|На обе стороны', 'rostov family apartment kitchen living room bedrooms bathroom'), ('Ростов-на-Дону', 'Ворошиловский', 'улица Евдокимова', '37', '112', 'apartment', 'sale', 1, 40.5, 19.2, 10.7, 10, 18, 5850000, 'Однокомнатная квартира в новом доме', 'Хороший ремонт, кухня с техникой, лоджия, закрытый двор и гостевая парковка.', 'Монолитный|Совмещённый|Лоджия|2 лифта|Наземная|Евро|Во двор', 'rostov one bedroom apartment modern kitchen bedroom balcony'), ('Екатеринбург', 'Центральный', 'улица Шейнкмана', '90', '105', 'apartment', 'sale', 3, 88.7, 51.2, 15, 14, 25, 12900000, 'Трёхкомнатная квартира в центре Екатеринбурга', 'Новый жилой комплекс, кухня-гостиная, две спальни, два санузла, большая лоджия и подземный паркинг.', 'Монолитный|2 санузла|Лоджия|2 лифта|Подземная|Дизайнерский|На обе стороны', 'yekaterinburg luxury apartment kitchen living room bedrooms bathroom'), ('Екатеринбург', 'ВИЗ', 'улица Татищева', '49', '72', 'apartment', 'sale', 2, 60.2, 34, 12.5, 8, 16, 8500000, 'Двухкомнатная квартира рядом с набережной', 'Современный дом, кухня-гостиная, спальня, лоджия, гардеробная и паркинг.', 'Монолитный|Совмещённый|Лоджия|2 лифта|Подземная|Евро|На улицу', 'yekaterinburg modern apartment kitchen living room bedroom balcony'), ('Екатеринбург', 'Академический', 'улица Краснолесья', '133', '226', 'apartment', 'rent', 1, 37.9, 18.1, 10, 12, 16, 36000, 'Однокомнатная квартира в аренду', 'Тёплая меблированная квартира с техникой, лоджией и гардеробной. Закрытый двор.', 'Монолитный|Совмещённый|Лоджия|2 лифта|Наземная|Евро|Во двор', 'yekaterinburg furnished rental apartment kitchen bedroom bathroom'), ('Нальчик', 'Центральный', 'проспект Ленина', '38', '27', 'apartment', 'sale', 3, 86.5, 50, 15.5, 4, 9, 8200000, 'Просторная квартира в центре Нальчика', 'Семейная квартира с большой кухней, тремя комнатами, лоджией и двумя санузлами. Рядом парк и школы.', 'Кирпичный|2 санузла|Лоджия|Есть|Наземная|Евро|На обе стороны', 'nalchik apartment family kitchen living room bedroom bathroom'), ('Нальчик', 'Долинск', 'улица Кулиева', '17', '63', 'apartment', 'sale', 2, 64.7, 36.2, 12.8, 5, 8, 6100000, 'Двухкомнатная квартира в спокойном районе', 'Хороший ремонт, просторная кухня, изолированные комнаты и балкон. Рядом зелёная зона и магазины.', 'Кирпичный|Раздельный|Есть|Есть|Наземная|Евро|Во двор', 'nalchik apartment interior kitchen living room bedroom balcony'), ('Нальчик', 'Александровка', 'улица Мальбахова', '81', '14', 'apartment', 'sale', 4, 112, 67, 18, 3, 7, 10900000, 'Большая четырёхкомнатная квартира', 'Кухня-гостиная, три спальни, два санузла, две лоджии и гардеробная. Подходит для большой семьи.', 'Монолитно-кирпичный|2 санузла|2 балкона|Есть|Наземная|Дизайнерский|На обе стороны', 'large family apartment luxury kitchen living room bedrooms bathroom'), ('Нальчик', 'Долинск', 'улица Кирова', '214', '', 'house', 'sale', 5, 185, 102, 22, 1, 2, 18900000, 'Двухэтажный дом с садом в Нальчике', 'Капитальный дом с кухней-гостиной, четырьмя спальнями, двумя санузлами, гаражом и садом.', 'Кирпичный|2 санузла|Есть|Нет|Наземная|Евро|На обе стороны', 'house exterior garden living room kitchen bedroom bathroom'), ('Краснодар', 'Прикубанский', 'улица Ягодная', '44', '', 'house', 'sale', 4, 156, 84, 20, 1, 2, 15900000, 'Современный загородный дом с террасой', 'Новый двухэтажный дом с кухней-гостиной, тремя спальнями, двумя санузлами и террасой. Благоустроенный участок.', 'Кирпичный|2 санузла|Есть|Нет|Наземная|Евро|На обе стороны', 'modern house exterior terrace garden kitchen living room bedroom'), ('Сочи', 'Адлерский', 'улица Православная', '28', '', 'house', 'sale', 5, 210, 118, 25, 1, 3, 38500000, 'Дом с панорамным видом на море', 'Трёхэтажный дом на склоне с панорамным видом. Большая гостиная, кухня, четыре спальни, три санузла, террасы и парковка.', 'Монолитный|2 санузла|2 балкона|Нет|Наземная|Дизайнерский|На улицу', 'sochi luxury house sea view terrace garden pool'), ('Москва', 'Троицкий', 'улица Центральная', '17', '', 'house', 'sale', 6, 245, 132, 28, 1, 2, 44900000, 'Семейный дом на благоустроенном участке', 'Просторный дом с кухней-гостиной, четырьмя спальнями, кабинетом, гаражом и террасой.', 'Кирпичный|2 санузла|Есть|Нет|Наземная|Дизайнерский|На обе стороны', 'luxury family house exterior garden kitchen living room bedrooms'), ('Санкт-Петербург', 'Пушкинский', 'улица Садовая', '11', '', 'house', 'sale', 5, 172, 96, 21, 1, 2, 21500000, 'Загородный дом недалеко от Санкт-Петербурга', 'Дом с гостиной с камином, кухней, четырьмя спальнями, двумя санузлами, террасой и садом.', 'Кирпичный|2 санузла|Есть|Нет|Наземная|Евро|На обе стороны', 'country house garden fireplace kitchen living room bedroom'), ('Казань', 'Советский', 'улица Заречная', '7', '', 'house', 'sale', 4, 148, 79, 19, 1, 2, 13200000, 'Коттедж с гаражом и террасой', 'Современный двухэтажный коттедж с кухней-гостиной, тремя спальнями, двумя санузлами, гаражом и террасой.', 'Кирпичный|2 санузла|Есть|Нет|Наземная|Евро|На обе стороны', 'modern cottage house exterior terrace kitchen living room bedrooms'), ('Краснодар', 'Фестивальный', 'улица Северная', '412', '5', 'commercial', 'sale', None, 96, None, None, 1, 8, 16500000, 'Коммерческое помещение на первой линии', 'Помещение свободного назначения с отдельным входом и витринными окнами. Под магазин, офис, салон или студию.', 'Монолитный|Совмещённый|Нет|Есть|Наземная|Косметический|На улицу', 'commercial property storefront office retail interior'), ('Москва', 'Басманный', 'улица Земляной Вал', '52', '1', 'commercial', 'rent', None, 74, None, None, 1, 7, 280000, 'Офисное помещение в центре Москвы', 'Готовый офис с отдельным входом, кабинетами, переговорной, кухней и санузлом.', 'Монолитный|Совмещённый|Нет|Есть|Подземная|Евро|На улицу', 'modern office interior meeting room reception'), ('Екатеринбург', 'Верх-Исетский', 'улица Крауля', '76', '2', 'commercial', 'sale', None, 118, None, None, 1, 10, 14200000, 'Коммерческое помещение под бизнес', 'Просторное помещение с витринными окнами, отдельным входом, подсобной зоной и санузлом.', 'Монолитный|Совмещённый|Нет|Есть|Наземная|Косметический|На улицу', 'commercial space shop storefront interior office'), ('Нальчик', 'Центральный', 'улица Шортанова', '14', '', 'land', 'sale', None, 1200, None, None, None, None, 5200000, 'Земельный участок под строительство дома', 'Ровный участок в спокойной части города. Удобный подъезд, рядом жилые дома и коммуникации.', '—|—|—|Нет|Наземная|—|—', 'land plot countryside house construction garden'), ('Краснодар', 'Прикубанский', 'улица Российская', '331', '', 'land', 'sale', None, 800, None, None, None, None, 3900000, 'Участок под строительство в развитом районе', 'Участок правильной формы рядом с жилой застройкой. Удобный подъезд, подходит под строительство частного дома.', '—|—|—|Нет|Наземная|—|—', 'land plot residential construction garden'), ('Сочи', 'Хостинский', 'улица Ялтинская', '8', '', 'townhouse', 'sale', 4, 142, 77, 18, 1, 2, 24500000, 'Таунхаус с террасой и видом на горы', 'Двухэтажный таунхаус в закрытом посёлке. Кухня-гостиная, три спальни, два санузла, терраса и собственная парковка.', 'Монолитный|2 санузла|Есть|Нет|Наземная|Дизайнерский|На обе стороны', 'sochi townhouse mountains terrace modern interior kitchen living room'), ('Москва', 'Куркино', 'улица Соколово-Мещерская', '28', '', 'townhouse', 'sale', 5, 198, 108, 23, 1, 3, 37900000, 'Трёхэтажный таунхаус в Куркино', 'Просторный таунхаус с кухней-гостиной, четырьмя спальнями, кабинетом, тремя санузлами, террасой и парковкой.', 'Монолитно-кирпичный|2 санузла|2 балкона|Нет|Наземная|Дизайнерский|На обе стороны', 'luxury townhouse exterior terrace kitchen living room bedroom'), ('Санкт-Петербург', 'Петроградский', 'Кронверкский проспект', '31', '12', 'apartment', 'sale', 4, 118, 70, 20, 4, 6, 36900000, 'Премиальная квартира в историческом центре', 'Высокие потолки, дизайнерский ремонт, кухня-гостиная, три спальни, два санузла и гардеробная.', 'Кирпичный|2 санузла|Есть|Есть|Наземная|Дизайнерский|На обе стороны', 'luxury saint petersburg apartment classic interior kitchen living room bedroom')]

# Two additional varied cards, bringing the catalog to exactly 50.
RAW += [('Казань', 'Вахитовский', 'улица Островского', '35', '64', 'apartment', 'sale', 4, 109.5, 63, 19, 7, 9, 21800000, 'Премиальная 4-комнатная квартира в центре Казани', 'Кухня-гостиная, три спальни, кабинет, два санузла, гардеробная, закрытый двор и паркинг.', 'Монолитно-кирпичный|2 санузла|Лоджия|2 лифта|Подземная|Дизайнерский|На обе стороны', 'kazan luxury apartment designer kitchen living room bedrooms'), ('Ростов-на-Дону', 'Советский', 'улица Малиновского', '78', '211', 'apartment', 'sale', 2, 52.6, 29.5, 10.2, 13, 20, 6950000, 'Двухкомнатная квартира в новом ЖК', 'Кухня-гостиная, отдельная спальня, лоджия, гардеробная, закрытая территория и подземный паркинг.', 'Монолитный|Совмещённый|Лоджия|2 лифта|Подземная|Евро|На улицу', 'rostov modern apartment kitchen living room bedroom balcony')]

FEATURE_KEYS = [
    'Тип дома',
    'Санузел',
    'Балкон',
    'Лифт',
    'Парковка',
    'Отопление',
    'Ремонт',
    'Окна',
]


def build_features(ptype, raw_features):
    """
    Преобразует старые 7 характеристик из RAW
    в правильные значения согласно FEATURE_CHOICES.

    RAW:
        Тип дома | Санузел | Балкон | Лифт | Парковка | Ремонт | Окна

    В старом RAW поле после парковки фактически означает Ремонт,
    поэтому отопление добавляем отдельно.
    """

    vals = raw_features.split('|')

    # В RAW сейчас 7 значений:
    # 0 Тип дома
    # 1 Санузел
    # 2 Балкон
    # 3 Лифт
    # 4 Парковка
    # 5 Ремонт
    # 6 Окна

    f = {}

    if len(vals) >= 7:
        f['Тип дома'] = vals[0]
        f['Санузел'] = vals[1]
        f['Балкон'] = vals[2]
        f['Лифт'] = vals[3]
        f['Парковка'] = vals[4]
        f['Ремонт'] = vals[5]
        f['Окна'] = vals[6]

    # ---------------------------------------------------------
    # Дополнительные характеристики
    # ---------------------------------------------------------

    if ptype in ('apartment', 'townhouse', 'house'):
        f['Отопление'] = random.choice([
            'Центральное',
            'Центральное',
            'Индивидуальное',
        ])

        f['Интернет'] = random.choice([
            'Есть',
            'Есть',
            'Оптоволокно',
        ])

        if ptype == 'apartment':
            f['Мебель'] = random.choice([
                'Без мебели',
                'Частично',
                'Кухня',
                'Полностью меблирована',
            ])
        else:
            f['Мебель'] = random.choice([
                'Без мебели',
                'Частично',
                'Кухня',
            ])

        f['Тип перекрытий'] = random.choice([
            'Железобетонные',
            'Железобетонные',
            'Смешанные',
        ])

        f['Высота потолков'] = random.choice([
            '2.5 – 2.7 м',
            '2.7 – 3 м',
            '2.7 – 3 м',
            'Более 3 м',
        ])

        if ptype == 'house':
            f['Газ'] = random.choice([
                'Есть',
                'Есть',
                'Нет',
            ])
        else:
            f['Газ'] = random.choice([
                'Нет',
                'Нет',
                'Есть',
            ])

        f['Мусоропровод'] = random.choice([
            'Есть',
            'Нет',
        ])

    elif ptype == 'commercial':
        f['Отопление'] = random.choice([
            'Центральное',
            'Индивидуальное',
        ])
        f['Интернет'] = random.choice([
            'Есть',
            'Оптоволокно',
        ])
        f['Мебель'] = random.choice([
            'Без мебели',
            'Частично',
        ])
        f['Тип перекрытий'] = 'Железобетонные'
        f['Высота потолков'] = random.choice([
            '2.7 – 3 м',
            'Более 3 м',
        ])
        f['Газ'] = 'Нет'
        f['Мусоропровод'] = random.choice([
            'Есть',
            'Нет',
        ])

    elif ptype == 'land':
        # Для земли характеристики здания не имеют смысла.
        f = {
            'Тип дома': '—',
            'Санузел': '—',
            'Балкон': '—',
            'Лифт': 'Нет',
            'Парковка': 'Наземная',
            'Отопление': 'Нет',
            'Ремонт': 'Без ремонта',
            'Окна': '—',
            'Интернет': 'Нет',
            'Мебель': 'Без мебели',
            'Тип перекрытий': '—',
            'Высота потолков': '—',
            'Газ': 'Нет',
            'Мусоропровод': 'Нет',
        }

    return f


def card(row):
    (
        city,
        district,
        street,
        building,
        apt,
        ptype,
        dtype,
        rooms,
        area,
        living,
        kitchen,
        floor,
        total,
        price,
        title,
        desc,
        features,
        tags,
    ) = row

    f = build_features(ptype, features)

    return {
        'city': city,
        'district': district,
        'street': street,
        'building': building,
        'apartment': apt,
        'property_type': ptype,
        'deal_type': dtype,
        'rooms': rooms,
        'area': area,
        'living': living,
        'kitchen': kitchen,
        'floor': floor,
        'total': total,
        'price': price,
        'title': title,
        'description': desc,
        'features': f,
        'tags': tags,
    }
    
CATALOG=[card(x) for x in RAW]

class Command(BaseCommand):
    help='Создаёт реалистичные тестовые данные CRM'
    
    def add_arguments(self,p):
        p.add_argument('--clear',action='store_true',help='Удалить тестовые данные перед созданием')
        p.add_argument('--no-photos',action='store_true',help='Не скачивать фотографии')
    def handle(self,*args,**opts):
        random.seed(SEED)
        if len(CATALOG)!=50: raise RuntimeError(f'Каталог должен содержать 50 объектов, сейчас {len(CATALOG)}')
        if opts['clear']:
            Task.objects.all().delete(); Deal.objects.all().delete(); ContactActivity.objects.all().delete(); Contact.objects.all().delete(); PropertyPhoto.objects.all().delete(); PropertyFeature.objects.all().delete(); Property.objects.all().delete()
            UserProfile.objects.filter(user__username__in=['manager','agent1','agent2','agent3']).delete(); User.objects.filter(username__in=['manager','agent1','agent2','agent3']).delete(); Agency.objects.filter(slug='test-agency').delete()
        agency,_=Agency.objects.get_or_create(slug='test-agency',defaults={'name':'NalchikHome','city':'Нальчик','phone':'+7 (8662) 123-45-67','email':'info@test-agency.ru','description':'Демо-агентство недвижимости для тестирования CRM.'})
        manager=self.user(agency,'manager','Алексей','Менеджеров','+7 (900) 111-22-33',UserProfile.Role.MANAGER,True)
        agents=[self.user(agency,'agent1','Иван','Риелторов','+7 (900) 222-33-44',UserProfile.Role.AGENT),self.user(agency,'agent2','Мария','Агентова','+7 (900) 333-44-55',UserProfile.Role.AGENT),self.user(agency,'agent3','Сергей','Продавцов','+7 (900) 444-55-66',UserProfile.Role.AGENT)]
        users=[manager]+agents
        self.stdout.write('Создаём 50 объектов...'); properties=[]
        for i,d in enumerate(CATALOG):
            prop=Property.objects.create(agency=agency,agent=agents[i%3],deal_type=d['deal_type'],property_type=d['property_type'],status=random.choices(['active','reserved','draft'],[80,15,5])[0],title=d['title'],description=d['description'],price=Decimal(str(d['price'])),price_currency='RUB',area_total=Decimal(str(d['area'])),area_living=Decimal(str(d['living'])) if d['living'] is not None else None,area_kitchen=Decimal(str(d['kitchen'])) if d['kitchen'] is not None else None,rooms_count=d['rooms'],floor=d['floor'],floors_total=d['total'],city=d['city'],district=d['district'],street=d['street'],building=str(d['building']),apartment=str(d['apartment']),is_published=random.random()<.85,is_exclusive=random.random()<.2,commission_percent=Decimal(str(random.choice([2,3,4,5]))))
            properties.append(prop)
            for k,v in d['features'].items(): PropertyFeature.objects.create(property=prop,key=k,value=v)
            if not opts['no_photos']: self.photos(prop,d['tags'],random.randint(4,6))
        contacts=[]; ctypes=[x[0] for x in Contact.ContactType.choices]; cstats=[x[0] for x in Contact.Status.choices]; sources=[x[0] for x in Contact.Source.choices]
        self.stdout.write('Создаём 100 контактов...')
        for i in range(100):
            first=NAMES[i%len(NAMES)]; last=LAST[(i*3)%len(LAST)]; agent=agents[i%3]; bmin=Decimal(random.choice([4,5,6,7,8,10]))*Decimal('1000000'); bmax=bmin+Decimal(random.choice([2,3,5,7]))*Decimal('1000000')
            c=Contact.objects.create(agency=agency,agent=agent,first_name=first,last_name=last,phone=f'+7 (9{random.randint(10,99)}) {random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}',email=f'client{i+1:03d}@mail.ru',contact_type=random.choice(ctypes),status=random.choice(cstats),source=random.choice(sources),budget_min=bmin,budget_max=bmax,notes=random.choice(NOTES),created_at=timezone.now()-timedelta(days=random.randint(0,120)))
            contacts.append(c)
            for _ in range(random.randint(1,3)): ContactActivity.objects.create(contact=c,agent=agent,activity_type=random.choice([x[0] for x in ContactActivity.ActivityType.choices]),description=random.choice(ACT),created_at=timezone.now()-timedelta(days=random.randint(0,60)))
        self.stdout.write('Создаём 30 сделок...'); stages=[x[0] for x in Deal.Stage.choices]
        for i,prop in enumerate(properties[:30]):
            stage=stages[i%len(stages)]; close=(timezone.now()-timedelta(days=random.randint(1,60))).date() if stage=='closed' else None
            Deal.objects.create(agency=agency,agent=agents[i%3],property=prop,buyer_contact=contacts[(i*2)%100],seller_contact=contacts[(i*2+1)%100],stage=stage,price_agreed=prop.price*Decimal(random.choice(['0.93','0.95','0.97','1.00'])),commission_total=prop.price*Decimal('.03'),deposit_amount=prop.price*Decimal('.05'),deposit_date=(timezone.now()-timedelta(days=random.randint(1,30))).date(),close_date=close,notes='Тестовая сделка для демонстрации CRM.')
        self.stdout.write('Создаём по 10 задач на каждого пользователя...')
        ttypes=[x[0] for x in Task.TaskType.choices]; priorities=[x[0] for x in Task.Priority.choices]
        for ui,user in enumerate(users):
            for ti in range(10):
                done=ti<3 and random.choice([True,False]); Task.objects.create(agency=agency,agent=user,contact=contacts[(ui*10+ti)%100],title=TASKS[(ui*10+ti)%len(TASKS)],task_type=random.choice(ttypes),priority=random.choice(priorities),due_date=timezone.now()+timedelta(days=ti-3+random.randint(-2,5)),is_done=done,done_at=timezone.now()-timedelta(days=random.randint(0,5)) if done else None)
        self.stdout.write(self.style.SUCCESS('Готово: 50 объектов, 100 контактов, 30 сделок, 40 задач.'))
        self.stdout.write('Логины: manager / agent1 / agent2 / agent3 | пароль: testpass123')
    @staticmethod
    def user(agency,username,first,last,phone,role,staff=False):
        u,created=User.objects.get_or_create(username=username,defaults={'email':f'{username}@test-agency.ru','first_name':first,'last_name':last,'agency':agency,'phone':phone,'is_staff':staff})
        if created: u.set_password('testpass123'); u.save()
        else:
            changed=False
            if u.agency_id!=agency.id: u.agency=agency; changed=True
            if staff and not u.is_staff: u.is_staff=True; changed=True
            if changed: u.save()
        UserProfile.objects.get_or_create(user=u,defaults={'role':role}); return u
        
    @staticmethod
    def photo_query(prop, tags):
        tags = tags.lower()

        if prop.property_type == 'apartment':
            if 'luxury' in tags:
                return 'luxury,apartment,interior'
            if 'modern' in tags:
                return 'modern,apartment,interior'
            return 'apartment,interior'

        if prop.property_type == 'house':
            if 'sea' in tags:
                return 'house,sea,view'
            if 'luxury' in tags:
                return 'luxury,house,exterior'
            return 'house,exterior,garden'

        if prop.property_type == 'townhouse':
            return 'townhouse,modern,exterior'

        if prop.property_type == 'commercial':
            if 'office' in tags:
                return 'office,interior'
            return 'commercial,interior'

        if prop.property_type == 'land':
            return 'land,garden,property'

        return 'realestate,property'
    
    def photos(self, prop, tags, count):
        query = self.photo_query(prop, tags)

        folder = os.path.join(
            tempfile.gettempdir(),
            f'crm_prop_{prop.pk}'
        )
        os.makedirs(folder, exist_ok=True)

        self.stdout.write(
            f'  Скачиваем фото для #{prop.pk}: {query}'
        )

        for i in range(count):
            try:
                seed = abs(hash(f'{prop.pk}-{i}-{SEED}')) % 1000000

                url = (
                    f'https://loremflickr.com/1200/800/'
                    f'{query}?lock={seed}'
                )

                self.stdout.write(
                    f'    URL: {url}'
                )

                request = urllib.request.Request(
                    url,
                    headers={
                        'User-Agent': 'Mozilla/5.0'
                    }
                )

                with urllib.request.urlopen(
                    request,
                    timeout=60
                ) as response:
                    data = response.read()

                self.stdout.write(
                    f'    Получено: {len(data)} bytes'
                )

                if not data:
                    raise RuntimeError('Сервер вернул пустой файл')

                path = os.path.join(
                    folder,
                    f'{i}.jpg'
                )

                with open(path, 'wb') as f:
                    f.write(data)

                with open(path, 'rb') as f:
                    photo = PropertyPhoto(
                        property=prop,
                        is_cover=(i == 0),
                        order=i
                    )

                    photo.image.save(
                        f'property_{prop.pk}_{i + 1}.jpg',
                        File(f),
                        save=True
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'    OK: property_{prop.pk}_{i + 1}.jpg'
                    )
                )

                os.unlink(path)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'    ОШИБКА фото #{i + 1}: '
                        f'{type(e).__name__}: {e}'
                    )
                )

        try:
            os.rmdir(folder)
        except OSError:
            pass