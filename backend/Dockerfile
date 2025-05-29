


# Файл: backend/Dockerfile

# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1 # Предотвращает создание .pyc файлов
ENV PYTHONUNBUFFERED 1     # Вывод Python идет напрямую в терминал (полезно для логов Docker)

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем системные зависимости, если они нужны (например, для PostGIS или др.)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей и устанавливаем их
# Копируем отдельно, чтобы использовать кэш слоев Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Копируем весь код приложения в рабочую директорию
COPY ./app /app/app
# COPY alembic.ini .      # Если используете Alembic
# COPY ./alembic /app/alembic # Если используете Alembic


# Открываем порт, который будет слушать FastAPI (Uvicorn)
EXPOSE 8000

# Команда для запуска приложения при старте контейнера
# Используем --host 0.0.0.0 чтобы приложение было доступно извне контейнера
# --reload полезен для разработки, чтобы сервер перезапускался при изменениях кода
# В продакшене --reload следует убрать и, возможно, увеличить число воркеров (--workers)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


