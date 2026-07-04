from rest_framework import serializers
from .models import Selection, SelectionItem
from apps.properties.serializers import PropertyListSerializer


class SelectionItemSerializer(serializers.ModelSerializer):
    property_detail = PropertyListSerializer(
        source='property', read_only=True
    )
    client_status_display = serializers.CharField(
        source='get_client_status_display', read_only=True
    )

    class Meta:
        model = SelectionItem
        fields = [
            'id', 'property', 'property_detail',
            'agent_comment', 'client_status',
            'client_status_display', 'order',
        ]


class SelectionSerializer(serializers.ModelSerializer):
    items = SelectionItemSerializer(many=True, read_only=True)
    contact_name = serializers.CharField(
        source='contact.full_name', read_only=True
    )
    agent_name = serializers.CharField(
        source='agent.get_full_name', read_only=True
    )
    public_url = serializers.SerializerMethodField()

    class Meta:
        model = Selection
        fields = [
            'id', 'title',
            'contact', 'contact_name',
            'agent_name', 'public_token', 'public_url',
            'items', 'created_at', 'updated_at',
        ]

    def get_public_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.get_public_url())
        return None

    def create(self, validated_data):
        request = self.context['request']
        validated_data['agency'] = request.user.agency
        validated_data['agent'] = request.user
        return super().create(validated_data)