import time

import requests
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.properties.models import Property


class Command(BaseCommand):
    help = "Геокодирует объекты недвижимости через OpenStreetMap Nominatim"

    def handle(self, *args, **options):
        qs = (
            Property.objects
            .filter(
                Q(latitude__isnull=True) |
                Q(longitude__isnull=True)
            )
            .exclude(city='')
            .order_by('created_at')
        )

        total = qs.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Найдено объектов для геокодирования: {total}"
            )
        )

        if total == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "Все объекты уже имеют координаты."
                )
            )
            return

        session = requests.Session()

        session.headers.update({
            "User-Agent": "RealEstateCRM/1.0 (real estate CRM)"
        })

        success = 0
        failed = 0

        for i, property in enumerate(qs, 1):

            parts = [
                property.street,
                property.building,
                property.district,
                property.city,
                "Россия",
            ]
            address = ", ".join(
                str(part).strip()
                for part in parts
                if part
            )

            self.stdout.write("")
            self.stdout.write(
                f"[{i}/{total}] {property.title}"
            )
            self.stdout.write(
                f"Адрес: {address}"
            )

            try:
                response = session.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": address,
                        "format": "json",
                        "limit": 1,
                        "countrycodes": "ru",
                    },
                    timeout=15,
                )

                response.raise_for_status()

                data = response.json()

                if data:
                    latitude = float(data[0]["lat"])
                    longitude = float(data[0]["lon"])

                    property.latitude = latitude
                    property.longitude = longitude

                    property.save(
                        update_fields=[
                            "latitude",
                            "longitude",
                        ]
                    )

                    success += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Найдено: "
                            f"{latitude:.7f}, {longitude:.7f}"
                        )
                    )

                else:
                    failed += 1

                    self.stdout.write(
                        self.style.WARNING(
                            "✗ Адрес не найден"
                        )
                    )

            except requests.RequestException as e:
                failed += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Ошибка запроса: {e}"
                    )
                )

            except (ValueError, KeyError, TypeError) as e:
                failed += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Ошибка обработки ответа: {e}"
                    )
                )

            except Exception as e:
                failed += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Неожиданная ошибка: {e}"
                    )
                )

            # Nominatim требует соблюдать ограничение по частоте запросов.
            if i < total:
                time.sleep(1.1)

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(
            self.style.SUCCESS(
                "ГЕОКОДИРОВАНИЕ ЗАВЕРШЕНО"
            )
        )
        self.stdout.write("=" * 50)

        self.stdout.write(
            f"Успешно:       {success}"
        )

        self.stdout.write(
            f"Не найдено:    {failed}"
        )

        self.stdout.write(
            f"Всего:         {total}"
        )
