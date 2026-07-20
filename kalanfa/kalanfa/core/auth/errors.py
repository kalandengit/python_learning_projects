from kalanfa.core.errors import KalanfaError
from kalanfa.core.errors import KalanfaValidationError


class InvalidRoleKind(KalanfaValidationError):
    pass


class UserDoesNotHaveRoleError(KalanfaError):
    pass


class UserIsNotFacilityUser(KalanfaError):
    pass


class UserIsNotMemberError(KalanfaError):
    pass


class IncompatibleDeviceSettingError(KalanfaError):
    pass


class InvalidMembershipError(KalanfaValidationError):
    pass


class InvalidCollectionHierarchy(KalanfaValidationError):
    pass


class NoAvailableSequences(KalanfaError):
    pass


class SequenceAlreadyAssigned(KalanfaError):
    pass
