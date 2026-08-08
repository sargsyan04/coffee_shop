# Coffee Shop

Бэкенд для кофейни на FastAPI: каталог напитков, корзина и заказы, аутентификация по JWT, роли (клиент / бариста / админ), бонусные баллы за заказы, отзывы на товары и загрузка изображений. Плюс простой фронтенд на HTML/CSS/JS, который со всем этим работает.

## Что внутри

- Регистрация с подтверждением email кодом, вход/выход, refresh-токены
- Восстановление пароля и повторная активация аккаунта (мягкое удаление вместо физического, с периодом на восстановление)
- Каталог: категории, товары, теги, загрузка фото товара, пагинация и сортировка списка товаров
- Корзина и оформление заказа, статусы заказа (created → paid → in_progress → ready → completed / cancelled)
- Панель для бариста — очередь активных заказов, смена статуса
- Панель администратора — пользователи (поиск, фильтры, сортировка, пагинация), роли, сброс пароля, базовая статистика по клиенту
- Бонусные баллы: процент от суммы заказа (ставка растёт вместе с суммой), надбавка за большой заказ и разовый бонус за первый завершённый заказ
- Отзывы на товары

## Стек

- **FastAPI** + Pydantic v2
- **SQLAlchemy 2.0** (async) + **Alembic** для миграций
- **PostgreSQL**
- JWT (PyJWT) + bcrypt для авторизации
- fastapi-mail для писем с кодом подтверждения (Jinja-шаблон в `src/templates`)
- Pillow — обработка загружаемых изображений
- Фронтенд — обычные HTML/CSS/JS-страницы без фреймворков, ходят в API через `fetch`

## Структура

```
src/
  core/        # конфиг, сессия БД, enum'ы, логирование, работа с файлами
  models/      # модели SQLAlchemy
  schemas/     # Pydantic-схемы
  routers/     # эндпоинты FastAPI
  services/    # бизнес-логика (авторизация, корзина, бонусы, письма)
  validators/  # зависимости FastAPI (текущий пользователь, роли, проверки)
  fixtures/    # тестовые/начальные данные, создание админа
  manage.py    # CLI: загрузка фикстур, создание суперпользователя
frontend/
  pages/       # HTML-страницы
  css/ js/     # стили и логика
alembic/       # миграции
```

## Запуск

Через Docker:

```bash
cp .env.example .env
# заполнить SECRET_KEY, DB_PASSWORD и при желании SMTP-данные для писем
docker-compose up --build
```

API поднимется на `http://localhost:8080`, документация — на `http://localhost:8080/docs`.

Без Docker (нужен PostgreSQL, DB_HOST в `.env` должен указывать на него, а не на `db`):

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m src.manage createsuperuser --use-fixture   # или без --use-fixture, интерактивно
uvicorn src.main:app --reload --port 8080
```

Фронтенд — статичные файлы в `frontend/`, их достаточно открыть через любой локальный сервер (например, Live Server) и настроить `CORS_ORIGINS` в `.env` под его порт.

### Полезные команды manage.py

```bash
python -m src.manage loaddata --models all          # накатить фикстуры
python -m src.manage loaddata --models all --force   # пересоздать, если уже есть
python -m src.manage createsuperuser                  # создать админа вручную
```

Дефолтный админ (`ADMIN_EMAIL` / `ADMIN_PASSWORD` из `.env`) создаётся автоматически при старте приложения, если в базе ещё нет ни одного администратора.

## Пагинация

Списочные эндпоинты (`GET /products/`, `GET /admin/users`) принимают `page` (по умолчанию 1) и `page_size` (по умолчанию 20, максимум 100) и отдают единый формат:

```json
{
  "items": [ /* ProductResponse / AdminUserResponse */ ],
  "total": 57,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

Список товаров дополнительно поддерживает `sort_by` (`name` / `price` / `rating` / `popularity`) и `order` (`asc` / `desc`); список пользователей — `sort_by` (`id` / `created_at` / `orders_count` / `total_spent` / `reviews_count`), `sort_order` (`asc` / `desc`) и фильтры (`search`, `role`, `is_active`, `is_email_verified`, `has_orders`, `has_reviews`).

## Роли

- `customer` — обычный клиент
- `barista` — видит очередь заказов и меняет их статус
- `admin` — управление пользователями и полный доступ

## Известные ограничения

Часть корзины ещё не доделана: обновление и удаление позиции (`PATCH /cart/items/{id}`, `DELETE /cart/items/{id}`) сейчас возвращают 501. Гостевой чекаут (`/cart/guest/checkout`) реализован на уровне сервиса, но роутер пока не подключён в `main.py` — фронтенд уже готов на него ходить, но нужно доделать логику на бэке (создание гостевого пользователя, пересчёт цены на сервере и т.д., детали см. в комментариях в `src/routers/guest_cart.py`).

## Лицензия

MIT
