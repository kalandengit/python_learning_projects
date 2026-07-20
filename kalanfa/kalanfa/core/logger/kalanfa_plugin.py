import logging

from kalanfa.core.auth.hooks import FacilityDataSyncHook
from kalanfa.core.auth.sync_operations import KalanfaVersionedSyncOperation
from kalanfa.core.logger.models import AttemptLog
from kalanfa.core.logger.models import ExamAttemptLog
from kalanfa.core.logger.models import ExamLog
from kalanfa.core.logger.utils.attempt_log_consolidation import (
    consolidate_quiz_attempt_logs,
)
from kalanfa.core.logger.utils.exam_log_migration import migrate_from_exam_logs
from kalanfa.plugins.hooks import register_hook

logger = logging.getLogger(__name__)


class ExamLogsCompatibilityOperation(KalanfaVersionedSyncOperation):
    version = "0.15.0"

    def upgrade(self, context):
        """
        Migrates exam logs to be backwards compatible with older Kalanfas
        :type context: morango.sync.context.LocalSessionContext
        """
        exam_logs_ids = context.transfer_session.get_touched_record_ids_for_model(
            ExamLog
        )
        exam_attempt_logs_ids = (
            context.transfer_session.get_touched_record_ids_for_model(ExamAttemptLog)
        )
        logger.info("Migrating {} ExamLogs records".format(len(exam_logs_ids)))
        migrate_from_exam_logs(
            ExamLog.objects.filter(id__in=exam_logs_ids),
            source_attempt_log_ids=exam_attempt_logs_ids,
        )


class AttemptLogsConsolidationOperation(KalanfaVersionedSyncOperation):
    version = "0.16.0"

    def upgrade(self, context):
        """
        Consolidates duplicate attempt logs synced from older Kalanfa versions
        :type context: morango.sync.context.LocalSessionContext
        """
        attempt_logs_ids = context.transfer_session.get_touched_record_ids_for_model(
            AttemptLog
        )
        logger.info(
            "Consolidating duplicates in {} AttemptLog records".format(
                len(attempt_logs_ids)
            )
        )
        consolidate_quiz_attempt_logs(
            AttemptLog.objects.filter(id__in=attempt_logs_ids)
        )


@register_hook
class LoggerSyncHook(FacilityDataSyncHook):
    cleanup_operations = [
        ExamLogsCompatibilityOperation(),
        AttemptLogsConsolidationOperation(),
    ]
