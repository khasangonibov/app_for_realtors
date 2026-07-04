from rest_framework import serializers
from .models import Contact, ContactActivity


class ContactActivitySerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(
        source='agent.get_full_name', read_only=True
    )
    activity_type_display = serializers.CharField(
        source='get_activity_type_display', read_only=True
    )

    class Meta:
        model = ContactActivity
        fields = [
            'id', 'activity_type', 'activity_type_display',
            'description', 'scheduled_at', 'is_done',
            'agent_name', 'created_at',
        ]
        read_only_fields = ['agent_name', 'created_at']


class ContactSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    contact_type_display = serializers.CharField(
        source='get_contact_type_display', read_only=True
    )
    activities = ContactActivitySerializer(many=True, read_only=True)

    class Meta:
        model = Contact
        fields = [
            'id', 'full_name',
            'first_name', 'last_name', 'middle_name',
            'phone', 'email',
            'contact_type', 'contact_type_display',
            'status', 'status_display',
            'source', 'budget_min', 'budget_max',
            'notes', 'activities',
            'created_at', 'updated_at',
        ]

    def create(self, validated_data):
        request = self.context['request']
        validated_data['agency'] = request.user.agency
        validated_data['agent'] = request.user
        return super().create(validated_data)