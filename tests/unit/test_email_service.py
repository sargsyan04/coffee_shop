import pytest
from fastapi_mail import ConnectionConfig

import src.services.email as email_service
from src.services.email import _get_mail_config, render_email


@pytest.fixture(autouse=True)
def _reset_cached_mail_config():
    """_conf is a module-level singleton, so tests would otherwise leak
    state (and mail config) into each other depending on run order.
    """
    email_service._conf = None
    yield
    email_service._conf = None


# render_email


def test_render_email_includes_the_verification_code():
    html = render_email("verify_email.html", code="123456")

    assert "123456" in html


def test_render_email_produces_html_content():
    html = render_email("verify_email.html", code="000000")

    assert "<table" in html


# _get_mail_config (lazy singleton)


def test_get_mail_config_not_built_until_first_call():
    assert email_service._conf is None


def test_get_mail_config_returns_connection_config():
    config = _get_mail_config()

    assert isinstance(config, ConnectionConfig)


def test_get_mail_config_is_cached_across_calls():
    first = _get_mail_config()
    second = _get_mail_config()

    # same object, not rebuilt on every call
    assert first is second


def test_get_mail_config_uses_settings_mail_from():
    config = _get_mail_config()

    assert str(config.MAIL_FROM) == email_service.settings.MAIL_FROM