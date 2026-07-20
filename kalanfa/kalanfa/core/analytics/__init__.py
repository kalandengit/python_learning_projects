try:
    import kalanfa.utils.pskalanfa  # noqa: F401

    SUPPORTED_OS = True
except NotImplementedError:
    # This module can't work on this OS
    SUPPORTED_OS = False
