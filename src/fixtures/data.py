from decimal import Decimal

from src.core import UserRole, settings

# Users


def get_super_admin_fixture() -> dict:
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
        {"name": "Drinks"},
        {"name": "Desserts"},
        {"name": "Food"},
    ]


# Tags


def get_tags_fixtures() -> list[dict]:
    return [
        {"name": "Bestseller", "slug": "bestseller"},
        {"name": "New", "slug": "new"},
        {"name": "Vegan", "slug": "vegan"},
    ]


# Products


def get_products_fixtures() -> list[dict]:
    return [
        {
            "name": "Cappuccino",
            "description": "Classic cappuccino made with semi-skimmed milk",
            "price": Decimal(1200),
            "category": "Drinks",
            "tags": ["bestseller"],
            "is_available": True,
        },
        {
            "name": "Latte",
            "description": "Smooth latte with velvety milk foam",
            "price": Decimal(1300),
            "category": "Drinks",
            "tags": [],
            "is_available": True,
        },
        {
            "name": "Raf coffee",
            "description": "Raf coffee with cream and vanilla syrup",
            "price": Decimal(1500),
            "category": "Drinks",
            "tags": ["new"],
            "is_available": True,
        },
        {
            "name": "New York Cheesecake",
            "description": "Classic cheesecake on a shortbread base",
            "price": Decimal(2200),
            "category": "Desserts",
            "tags": ["bestseller"],
            "is_available": True,
        },
        {
            "name": "Oatmeal Cookie",
            "description": "Homemade cookie with rolled oats",
            "price": Decimal(800),
            "category": "Desserts",
            "tags": ["vegan"],
            "is_available": True,
        },
        {
            "name": "Chicken Sandwich",
            "description": "Sandwich with chicken breast and fresh vegetables",
            "price": Decimal(2800),
            "category": "Food",
            "tags": [],
            "is_available": True,
        },
    ]
