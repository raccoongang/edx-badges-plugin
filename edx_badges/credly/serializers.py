from rest_framework import serializers


class BadgeDataModel(serializers.Serializer):  # pylint: disable=abstract-method
    id = serializers.CharField()
    state = serializers.CharField()
