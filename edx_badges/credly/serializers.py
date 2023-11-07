from rest_framework import serializers


class BadgeTemplateSchema(serializers.Serializer):  # pylint: disable=abstract-method
    name = serializers.CharField()

    class Meta:
        read_only_fields = "__all__"


class BadgeDataModel(serializers.Serializer):  # pylint: disable=abstract-method
    id = serializers.CharField()
    state = serializers.CharField()
    badge_template = BadgeTemplateSchema(source="*")

    class Meta:
        read_only_fields = "__all__"
