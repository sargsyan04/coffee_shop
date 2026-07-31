from src.fixtures.data import get_categories_fixtures, get_products_fixtures, get_super_admin_fixture, get_tags_fixtures, get_users_fixtures
from src.fixtures.loader import LOADERS, load_all, load_categories, load_products, load_super_admin, load_tags, load_users

__all__ = (
    "LOADERS",
    "get_categories_fixtures",
    "get_products_fixtures",
    "get_super_admin_fixture",
    "get_tags_fixtures",
    "get_users_fixtures",
    "load_all",
    "load_categories",
    "load_products",
    "load_super_admin",
    "load_tags",
    "load_users",
)
