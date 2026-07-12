from django.test import TestCase

from kalanfa.plugins.hooks import register_hook
from kalanfa.plugins.user_auth.hooks import LoginItemHook
from kalanfa.plugins.user_auth.kalanfa_plugin import UserAuthAsset


class UserAuthAssetPluginDataTestCase(TestCase):
    def test_no_login_items_registered(self):
        self.assertEqual(UserAuthAsset().plugin_data["loginItems"], [])

    def test_login_items_registered(self):
        class FakeLoginItem(LoginItemHook):
            label = "Sign in with Fake"
            url = "/fake/login/"
            icon_url = "/static/fake/icon.svg"

        FakeLoginItem.__module__ = "test.kalanfa_plugin"
        hook_cls = register_hook(FakeLoginItem)
        hook_cls.add_hook_to_registries()
        self.addCleanup(hook_cls.remove_hook_from_registries)
        self.assertEqual(
            UserAuthAsset().plugin_data["loginItems"],
            [hook_cls().data],
        )
