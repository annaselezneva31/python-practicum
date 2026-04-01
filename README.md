# Python Практикум

## Описание проекта
Базовый сервис на FastAPI, который хранит «факты» в PostgreSQL и предоставляет API для получения последних и недавних фактов. Проект уже содержит заготовки под кэш Redis, Celery, метрики FastAPI и структуру для расширения.

- API:
  - `GET /` — health-check
  - `GET /api/v1/facts/latest` — получить последний факт (нужно добавить кэш Redis)
  - `GET /api/v1/facts?limit&offset` — получить список последних фактов

## Что уже есть в коде
- Модель `Fact` и репозиторий `FactRepository` с методами `create`, `get_latest`, `get_recent`
- Конфиг через `pydantic-settings` (`app/core/config.py`) с URL БД, Redis и внешним API
- Заготовка под Redis-кэш (`app/services/cache.py`) — нужно реализовать
- Заготовка Celery-приложения (`app/core/celery_app.py`) и таски (`app/tasks/facts.py`) — нужно реализовать
- Инициализация БД при старте, FastAPI метрики через `prometheus_fastapi_instrumentator`

## Задания

1) Добавить `uv` для управления зависимостями
- Инициализировать проект и зафиксировать версии зависимостей
- Настроить скрипты запуска (app, worker, beat, тесты, линт)

2) Сделать кэширование через Redis для ручки `/api/v1/facts/latest`
- Использовать Redis как источник истины для «последнего факта» на короткий TTL
- При промахе кэша идти в БД и обновлять кэш

3) Реализовать Celery таску `fetch_and_store_fact` и автоматический запуск через Celery Beat
- Таска должна забирать случайный факт из `settings.external_fact_api` и сохранять в БД
- Продумать идемпотентность/обработку ошибок

4) Написать юнит-тесты и интеграционные тесты для ручек с `pytest` и `testcontainers`
- Юнит-тесты: репозиторий, кэш-слой
- Интеграция: фактические HTTP-запросы к API, БД в контейнере, Redis в контейнере

5) Добавить линтинг через `ruff`
- Настроить команды проверки/исправления

6) Добавить GitHub Workflow (линт + тест)
- CI отрабатывать по пушу на ветку

7) Реализовать сборку контейнера приложения и развертывание всего проекта через `docker` и `docker-compose`
- Отдельные сервисы: api, worker (celery), beat (celery beat), postgres, redis, prometheus, grafana, celery-exporter

8) Собрать метрики
- FastAPI метрики уже подключены — экспонировать для Prometheus
- Метрики Celery через `celery-exporter`
- Сделать дашборд Grafana с графиками по запросам API и задачам Celery

Задание со звёздочкой:
- Добавить авторизацию на основе материала из видео и защитить ручки/эндпоинты: [YouTube](https://youtu.be/QacZVserfIU)

---

## Полезные переменные окружения (.env)
```
FACT_DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/facts
FACT_REDIS_URL=redis://redis:6379
FACT_CELERY_BROKER_URL=redis://redis:6379
FACT_CELERY_RESULT_BACKEND=redis://redis:6379
FACT_FETCH_INTERVAL_SECONDS=20
FACT_EXTERNAL_FACT_API=https://uselessfacts.jsph.pl/api/v2/facts/random?language=en
```

## Структура проекта (основное)
```
app/
  api/v1/facts.py          # эндпоинты /latest и список
  core/config.py           # настройки
  core/celery_app.py       # инициализация Celery (реализовать)
  db/models.py             # модель Fact
  db/repository.py         # репозиторий FactRepository
  db/session.py            # движок и сессии
  schemas/fact.py          # схемы ответа
  services/cache.py        # Redis-кэш (реализовать)
  tasks/facts.py           # Celery таска (реализовать)
  main.py                  # FastAPI app + метрики
```
