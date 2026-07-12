from django_filters.rest_framework import CharFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import NumberFilter
from rest_framework import serializers

from kalanfa.core.api import ReadOnlyValuesViewset
from kalanfa.core.auth.permissions import KalanfaAuthPermissions
from kalanfa.core.auth.permissions import KalanfaAuthPermissionsFilter
from kalanfa.core.content.api import OptionalPageNumberPagination

from ..models import AttemptLog
from .filters import BaseLogFilter


class AttemptLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttemptLog
        fields = (
            "id",
            "item",
            "start_timestamp",
            "end_timestamp",
            "completion_timestamp",
            "time_spent",
            "complete",
            "correct",
            "hinted",
            "answer",
            "simple_answer",
            "interaction_history",
            "user",
            "error",
            "masterylog",
            "sessionlog",
        )


class AttemptLogDiffSerializer(AttemptLogSerializer):
    diff__correct = serializers.IntegerField(allow_null=True, read_only=True)

    class Meta(AttemptLogSerializer.Meta):
        fields = AttemptLogSerializer.Meta.fields + ("diff__correct",)


class AttemptFilter(BaseLogFilter):
    content = CharFilter(method="filter_content")
    mastery_level = NumberFilter(field_name="masterylog__mastery_level")

    def filter_content(self, queryset, name, value):
        return queryset.filter(masterylog__summarylog__content_id=value)

    class Meta:
        model = AttemptLog
        fields = ["masterylog", "complete", "user", "content", "item", "mastery_level"]


class AttemptLogViewSet(ReadOnlyValuesViewset):
    permission_classes = (KalanfaAuthPermissions,)
    filter_backends = (
        KalanfaAuthPermissionsFilter,
        DjangoFilterBackend,
    )
    queryset = AttemptLog.objects.all()
    pagination_class = OptionalPageNumberPagination
    filterset_class = AttemptFilter
    serializer_class = AttemptLogSerializer
