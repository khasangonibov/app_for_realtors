import os
import random
import tempfile
import urllib.request

from django.core.files import File
from django.core.management.base import BaseCommand

from apps.properties.models import Property, PropertyPhoto


SEED = 20260814


class Command(BaseCommand):
    help = "Добавляет фотографии существующим объектам недвижимости."

    def photo_query(self, prop):
        if prop.property_type == "apartment":
            return "apartment,interior"

        if prop.property_type == "house":
            return "house,exterior,garden"

        if prop.property_type == "commercial":
            return "commercial,interior"

        if prop.property_type == "land":
            return "land,garden,property"

        return "realestate,property"

    def handle(self, *args, **options):
        random.seed(SEED)

        properties = Property.objects.all().order_by("created_at", "pk")
        total = properties.count()

        self.stdout.write(
            self.style.SUCCESS(f"Найдено объектов: {total}")
        )

        created_total = 0

        for index, prop in enumerate(properties, 1):
            existing = PropertyPhoto.objects.filter(property=prop).count()

            if existing:
                self.stdout.write(
                    f"[{index}/{total}] #{prop.pk}: уже есть {existing} фото — пропуск"
                )
                continue

            count = random.randint(4, 6)
            query = self.photo_query(prop)

            self.stdout.write(
                f"[{index}/{total}] #{prop.pk}: {count} фото → {query}"
            )

            folder = os.path.join(
                tempfile.gettempdir(),
                f"crm_prop_{prop.pk}"
            )
            os.makedirs(folder, exist_ok=True)

            for i in range(count):
                try:
                    seed = abs(hash(f"{prop.pk}-{i}-{SEED}")) % 1000000

                    url = (
                        f"https://loremflickr.com/1200/800/"
                        f"{query}?lock={seed}"
                    )

                    request = urllib.request.Request(
                        url,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )

                    with urllib.request.urlopen(
                        request,
                        timeout=60
                    ) as response:
                        data = response.read()

                    if not data:
                        raise RuntimeError("Пустой ответ")

                    path = os.path.join(folder, f"{i}.jpg")

                    with open(path, "wb") as f:
                        f.write(data)

                    with open(path, "rb") as f:
                        photo = PropertyPhoto(
                            property=prop,
                            is_cover=(i == 0),
                            order=i,
                        )

                        photo.image.save(
                            f"property_{prop.pk}_{i + 1}.jpg",
                            File(f),
                            save=True,
                        )

                    created_total += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    OK: property_{prop.pk}_{i + 1}.jpg"
                        )
                    )

                    os.unlink(path)

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"    ОШИБКА #{i + 1}: "
                            f"{type(e).__name__}: {e}"
                        )
                    )

            try:
                os.rmdir(folder)
            except OSError:
                pass

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Добавлено фотографий: {created_total}"
            )
        )
