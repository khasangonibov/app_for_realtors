FROM python:3.12-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Сначала копируем requirements (кэш слоёв Docker)
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Копируем весь проект
COPY . .

# Создаём папки
RUN mkdir -p staticfiles media

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]