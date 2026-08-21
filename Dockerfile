FROM python:3.12-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Сначала копируем requirements (кэш слоёв Docker)
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/development.txt

# Копируем весь проект
COPY . .

# Создаём папки
RUN mkdir -p staticfiles media

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

# RUN apk update && \
#     apk add --no-cache tzdata && \
#     apk add --no-cache locales && \
#     localedef -i en_US -f UTF-8 en_US.UTF-8