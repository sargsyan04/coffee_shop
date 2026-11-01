# Coffee Shop

A coffee shop backend built with FastAPI: a drinks catalog, cart and orders, JWT authentication, roles (customer / barista / admin), bonus points for orders, product reviews and image uploads. It also includes a simple HTML/CSS/JS frontend that works with all of it.

## Features

- Registration with an email confirmation code, login/logout, refresh tokens
- Password recovery and account reactivation (soft delete instead of physical deletion, with a grace period for restoring the account)
- Catalog: categories, products, tags, product photo upload, pagination and sorting of the product list
- Cart and checkout, order statuses (created → paid → in_progress → ready → completed / cancelled)
- Barista panel: queue of active orders, status changes
- Admin panel: users (search, filters, sorting, pagination), roles, password reset, basic per-customer statistics
- Bonus points: a percentage of the order total (the rate grows with the total), a bonus for large orders and a one-time bonus for the first completed order
- Product reviews

## Tech stack

- **FastAPI** + Pydantic v2
- **SQLAlchemy 2.0** (async) + **Alembic** for migrations
- **PostgreSQL**
- JWT (PyJWT) + bcrypt for authentication
- fastapi-mail for confirmation code emails (Jinja template in `src/templates`)
- Pillow for processing uploaded images
- Frontend: plain HTML/CSS/JS pages without frameworks, talking to the API via `fetch`

## Project structure

```
src/
  core/        # config, DB session, enums, logging, file handling
  models/      # SQLAlchemy models
  schemas/     # Pydantic schemas
  routers/     # FastAPI endpoints
  services/    # business logic (auth, cart, bonuses, emails)
  validators/  # FastAPI dependencies (current user, roles, checks)
  fixtures/    # sample/initial data, admin creation
  manage.py    # CLI: loading fixtures, creating a superuser
frontend/
  pages/       # HTML pages
  css/ js/     # styles and logic
migrations/    # Alembic migrations
```

## Getting started

With Docker:

```bash
cp .env.example .env
# fill in SECRET_KEY, DB_PASSWORD and, optionally, SMTP settings for emails
docker-compose up --build
```

The API starts at `http://localhost:8080`, the documentation is at `http://localhost:8080/docs`.

Without Docker (requires PostgreSQL; `DB_HOST` in `.env` must point to it, not to `db`):

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt   # requirements.txt alone is enough to run the app
alembic upgrade head
python -m src.manage createsuperuser --use-fixture   # or without --use-fixture for interactive mode
uvicorn src.main:app --reload --port 8080
```

The frontend is a set of static files in `frontend/`. Open them through any local server (for example, Live Server) and set `CORS_ORIGINS` in `.env` to match its port.

### Useful manage.py commands

```bash
python -m src.manage loaddata --models all          # load fixtures
python -m src.manage loaddata --models all --force   # recreate if they already exist
python -m src.manage createsuperuser                  # create an admin manually
```

The default admin (`ADMIN_EMAIL` / `ADMIN_PASSWORD` from `.env`) is created automatically on application startup if the database has no administrator yet.

## Pagination

List endpoints (`GET /products/`, `GET /admin/users`) accept `page` (default 1) and `page_size` (default 20, maximum 100) and return a unified format:

```json
{
  "items": [ /* ProductResponse / AdminUserResponse */ ],
  "total": 57,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

The product list additionally supports `sort_by` (`name` / `price` / `rating` / `popularity`) and `order` (`asc` / `desc`). The user list supports `sort_by` (`id` / `created_at` / `orders_count` / `total_spent` / `reviews_count`), `sort_order` (`asc` / `desc`) and filters (`search`, `role`, `is_active`, `is_email_verified`, `has_orders`, `has_reviews`).

## Roles

- `customer`: a regular customer
- `barista`: sees the order queue and changes order statuses
- `admin`: user management and full access

## Known limitations

Payment is currently a stub: an order gets the `paid` status immediately at checkout. Real-time notifications, background tasks (Celery + RabbitMQ) and WebSocket support are planned.

## License

MIT
