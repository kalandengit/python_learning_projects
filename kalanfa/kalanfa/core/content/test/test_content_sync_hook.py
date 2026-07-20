import mock
from morango.sync.context import SessionContext

from kalanfa.core.auth.sync_operations import KalanfaSyncOperations
from kalanfa.core.content.kalanfa_plugin import ContentSyncHook
from kalanfa.core.content.test.utils.test_content_request import (
    BaseIncompleteDownloadsQuerysetTestCase,
)
from kalanfa.core.device.models import DeviceStatus


class KalanfaContentSyncHookTestCase(BaseIncompleteDownloadsQuerysetTestCase):
    def setUp(self):
        super().setUp()
        self.operation = KalanfaSyncOperations()
        self.context = mock.Mock(spec_set=SessionContext)()

    @mock.patch("kalanfa.core.device.models.LearnerDeviceStatus.save_learner_status")
    @mock.patch("kalanfa.core.content.utils.content_request.StorageCalculator")
    def test_post_transfer_sets_insufficient_storage(
        self,
        mock_calc,
        mock_save_learner_status,
    ):
        with mock.patch(
            "kalanfa.core.content.utils.settings.automatic_download_enabled",
            return_value=True,
        ):
            with mock.patch(
                "kalanfa.core.content.utils.content_request.get_free_space_for_downloads",
                return_value=0,
            ):
                self._create_resources(self.admin_request.contentnode_id)
                hook = ContentSyncHook()
                hook.post_transfer(
                    self.facility.dataset_id,
                    True,
                    True,
                    self.learner.id,
                    self.context,
                )
                mock_save_learner_status.assert_called_with(
                    self.learner.id, DeviceStatus.InsufficientStorage
                )
