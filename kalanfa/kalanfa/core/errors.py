from django.core.exceptions import ValidationError


class KalanfaError(Exception):
    pass


class KalanfaValidationError(ValidationError, KalanfaError):
    pass


class KalanfaUpgradeError(KalanfaError):
    """
    Should be used whenever an error arises that is due to an anticipated future incompatible change,
    for example: change in content database schemas, change in content that is not supported by old versions
    of Kalanfa.
    """

    pass


class RedisConnectionError(Exception):
    pass
