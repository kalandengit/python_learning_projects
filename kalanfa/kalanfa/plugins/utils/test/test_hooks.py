from inspect import isabstract

import pytest

from kalanfa.plugins import hooks


@hooks.define_hook
class HookAbstract(hooks.KalanfaHook):
    pass


@hooks.define_hook(only_one_registered=True)
class SingleHookAbstract(hooks.KalanfaHook):
    pass


class Hook(HookAbstract):
    pass


class SingleHook(SingleHookAbstract):
    pass


def test_register_hook_not_kalanfa_plugin():
    try:
        hooks.register_hook(Hook)
        pytest.fail(
            "Allowed a hook defined outside of a kalanfa_plugin module to be registered"
        )
    except RuntimeError:
        pass


@pytest.fixture
def valid_hook():
    original_module = Hook.__module__
    Hook.__module__ = "test.kalanfa_plugin"
    yield Hook
    Hook.__module__ = original_module


@pytest.fixture
def valid_single_hook():
    original_module = SingleHook.__module__
    SingleHook.__module__ = "test.kalanfa_plugin"
    yield SingleHook
    SingleHook.__module__ = original_module


def test_register_hook_kalanfa_plugin(valid_hook):
    hooks.register_hook(valid_hook)


def test_defined_hook_abstract():
    assert isabstract(HookAbstract)


def test_register_hook_single_hook(valid_single_hook):
    hooks.register_hook(valid_single_hook)


def test_register_multiple_hook_single_hook(valid_single_hook):
    valid_single_hook = hooks.register_hook(valid_single_hook)
    valid_single_hook.add_hook_to_registries()

    class OtherSingleHook(SingleHookAbstract):
        pass

    OtherSingleHook.__module__ = "test.kalanfa_plugin"
    try:
        OtherSingleHook = hooks.register_hook(OtherSingleHook)
        OtherSingleHook.add_hook_to_registries()
        pytest.fail(
            "Allowed a hook single instance hook to be registered more than once"
        )
    except hooks.HookSingleInstanceError:
        pass


def test_singleton_hook(valid_hook):
    valid_hook = hooks.register_hook(valid_hook)
    assert valid_hook() is valid_hook()


def test_get_hook(valid_hook):
    valid_hook = hooks.register_hook(valid_hook)
    valid_hook.add_hook_to_registries()
    hook = valid_hook()
    assert HookAbstract.get_hook(hook.unique_id) is hook


def test_registered_hooks(valid_hook):
    valid_hook = hooks.register_hook(valid_hook)
    valid_hook.add_hook_to_registries()
    hook = valid_hook()
    assert hook in HookAbstract.registered_hooks
    assert len(list(HookAbstract.registered_hooks)) == 1
