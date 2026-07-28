#!/usr/bin/env python3
"""
Management CLI for the Coffee Shop Management System.

Usage examples:
    python manage.py loaddata --models all
    python manage.py loaddata --models users categories
    python manage.py loaddata --models all --force
    python manage.py createsuperuser
    python manage.py createsuperuser --email admin@x.com --password Secret123 --name "Ada Lovelace"
    python manage.py createsuperuser --use-fixture
"""

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import select

from src.core import UserRole, session_factory
from src.fixtures import LOADERS, get_super_admin_fixture, load_all, load_super_admin
from src.models import User
from src.services import hash_password


async def _run_loaddata(models: list[str], force: bool) -> None:
    async with session_factory() as session:
        try:
            if "all" in models:
                await load_all(session, force=force)
            else:
                for model_name in models:
                    loader = LOADERS.get(model_name)
                    if loader is None:
                        print(f"[error] unknown model: '{model_name}'. Available: {', '.join(LOADERS.keys())}, all")
                        continue
                    print(f"Loading {model_name}...")
                    await loader(session, force=force)

            await session.commit()
            print("\nDone.")
        except Exception:
            await session.rollback()
            raise


async def _run_createsuperuser(args: argparse.Namespace) -> None:
    async with session_factory() as session:
        try:
            if args.use_fixture:
                user = await load_super_admin(session, force=args.force)
                await session.commit()
                print(f"\nSuper admin ready: {user.email}")
                return

            email = args.email or input("Email: ").strip()
            name = args.name or input("Name: ").strip()
            password = args.password or getpass.getpass("Password: ")

            if not password or len(password) < 8:
                print("Password must be at least 8 characters long.", file=sys.stderr)
                sys.exit(1)

            existing = await session.scalar(select(User).where(User.email == email))
            if existing:
                if not args.force:
                    print(f"User with email '{email}' already exists. Use --force to replace it.")
                    sys.exit(1)
                await session.delete(existing)
                await session.flush()

            user = User(
                name=name,
                email=email,
                hashed_password=hash_password(password).decode("utf-8"),
                is_active=True,
                is_email_verified=True,
                role=UserRole.ADMIN,
            )
            session.add(user)
            await session.commit()
            print(f"\nSuper admin created: {email}")
        except Exception:
            await session.rollback()
            raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manage.py",
        description="Management commands for the Coffee Shop database.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    loaddata_parser = subparsers.add_parser("loaddata", help="Load fixture data into the database.")
    loaddata_parser.add_argument(
        "--models",
        nargs="+",
        choices=["all", *LOADERS.keys()],
        default=["all"],
        help="Which fixture groups to load (default: all).",
    )
    loaddata_parser.add_argument(
        "--force",
        action="store_true",
        help="Delete and recreate rows that already exist (matched by natural key).",
    )

    superuser_parser = subparsers.add_parser("createsuperuser", help="Create an admin user.")
    superuser_parser.add_argument("--email", help="Email address for the admin.")
    superuser_parser.add_argument("--password", help="Password for the admin.")
    superuser_parser.add_argument("--name", help="Full name.")
    superuser_parser.add_argument(
        "--use-fixture",
        action="store_true",
        help=("Ignore --email/--password/--name and create the default admin " f"fixture ({get_super_admin_fixture()['email']})."),
    )
    superuser_parser.add_argument(
        "--force",
        action="store_true",
        help="Replace the user if one with the same email already exists.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "loaddata":
        asyncio.run(_run_loaddata(args.models, args.force))
    elif args.command == "createsuperuser":
        asyncio.run(_run_createsuperuser(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
