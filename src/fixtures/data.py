from decimal import Decimal

from src.core import UserRole, settings

# Users


def get_super_admin_fixture() -> dict:
    """The single default admin account, created via `manage.py createsuperuser`
    or as part of `manage.py loaddata --models users`."""
    return {
        "name": settings.ADMIN_NAME,
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD,  # plaintext — hashed by the loader
        "is_active": True,
        "is_email_verified": True,
        "must_change_password": True,
        "role": UserRole.ADMIN,
    }


def get_users_fixtures() -> list[dict]:
    return [
        {
            "name": "John",
            "email": "john@yopmail.com",
            "password": "johnbarista",
            "phone": "+37477202020",
            "role": UserRole.BARISTA,
            "is_active": True,
            "is_email_verified": True,
        },
        {
            "name": "Anna",
            "email": "anna@yopmail.com",
            "password": "annacustomer",
            "phone": "+37477303030",
            "role": UserRole.CUSTOMER,
            "is_active": True,
            "is_email_verified": True,
        },
    ]


# Categories


def get_categories_fixtures() -> list[dict]:
    return [
        {"name": "Напитки"},
        {"name": "Десерты"},
        {"name": "Еда"},
    ]


# Tags


def get_tags_fixtures() -> list[dict]:
    return [
        {"name": "Хит продаж", "slug": "bestseller"},
        {"name": "Новинка", "slug": "new"},
        {"name": "Веган", "slug": "vegan"},
    ]


# Products
# "category" references Category.name, "tags" references Tag.slug —
# the loader resolves these to real foreign keys after categories/tags exist


def get_products_fixtures() -> list[dict]:
    return [
        {
            "name": "Капучино",
            "description": "Классический капучино на молоке средней жирности",
            "price": Decimal(1200),
            "category": "Напитки",
            "tags": ["bestseller"],
            "is_available": True,
            "image_url": "/media/products/Product_7-f7686f2bddae4885b0329ceed7316f50.jpg",
        },
        {
            "name": "Латте",
            "description": "Мягкий латте с бархатной молочной пенкой",
            "price": Decimal(1300),
            "category": "Напитки",
            "tags": [],
            "is_available": True,
            "image_url": "/media/products/Product_8-a45a395cd465412fa05c93c84b3d0990.jpg",
        },
        {
            "name": "Раф",
            "description": "Раф на сливках с ванильным сиропом",
            "price": Decimal(1500),
            "category": "Напитки",
            "tags": ["new"],
            "is_available": True,
            "image_url": "/media/products/Product_9-73bf6b9a15274b5881dda9d86d2b5848.jpg",
        },
        {
            "name": "Чизкейк Нью-Йорк",
            "description": "Классический чизкейк на песочной основе",
            "price": Decimal(2200),
            "category": "Десерты",
            "tags": ["bestseller"],
            "is_available": True,
            "image_url": "/media/products/Product_10-5ba161d221a54504bd9c28dbedfc4e27.jpg",
        },
        {
            "name": "Овсяное печенье",
            "description": "Домашнее печенье с овсяными хлопьями",
            "price": Decimal(800),
            "category": "Десерты",
            "tags": ["vegan"],
            "is_available": True,
            "image_url": "/media/products/Product_11-5b1d540f33a24ba89816682f507dd243.jpg",
        },
        {
            "name": "Сэндвич с курицей",
            "description": "Сэндвич с куриной грудкой и свежими овощами",
            "price": Decimal(2800),
            "category": "Еда",
            "tags": [],
            "is_available": True,
            "image_url": "/media/products/Product_12-3f2068c3d4314c0cad1f50a0fd1495c2.jpg",
        },
    ]
