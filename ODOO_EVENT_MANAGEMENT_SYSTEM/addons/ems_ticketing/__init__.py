import logging
import secrets

from . import models
from .models.ticket import QR_SECRET_PARAM

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Provision a random QR signing secret on first install.

    No secret ships in the repository: the value is generated here with
    ``secrets.token_urlsafe`` so a fresh database is usable without an operator
    pasting a key, while nothing predictable is ever committed. Rotating the
    parameter later invalidates every outstanding QR envelope.
    """
    params = env["ir.config_parameter"].sudo()
    if not params.get_param(QR_SECRET_PARAM):
        params.set_param(QR_SECRET_PARAM, secrets.token_urlsafe(48))
        _logger.info("Generated a random EMS QR signing secret in %s", QR_SECRET_PARAM)
