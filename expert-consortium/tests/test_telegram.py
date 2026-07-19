from unittest.mock import patch

from app.bots.telegram_bot import is_allowed
from app.config import settings


def test_no_allowlist_means_nobody_allowed():
    with patch.object(settings, "telegram_allowed_user_id", ""):
        assert is_allowed(12345) is False


def test_only_configured_user_allowed():
    with patch.object(settings, "telegram_allowed_user_id", "42"):
        assert is_allowed(42) is True
        assert is_allowed(43) is False
        assert is_allowed(None) is False


def test_bot_requires_token():
    import pytest

    from app.bots.telegram_bot import build_application

    with patch.object(settings, "telegram_bot_token", ""):
        with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
            build_application()
