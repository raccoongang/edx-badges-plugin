from rest_framework import serializers


class BadgeStateChangedSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    id = serializers.CharField()
    organization_id = serializers.CharField()
    event_type = serializers.CharField()
    occurred_at = serializers.CharField()
