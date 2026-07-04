from rest_framework import serializers
from .models import Deal


class DealSerializer(serializers.ModelSerializer):
    stage_display = serializers.CharField(
        source='get_stage_display', read_only=True
    )
    property_info = serializers.SerializerMethodField()
    buyer_name = serializers.CharField(
        source='buyer_contact.full_name', read_only=True
    )
    agent_name = serializers.CharField(
        source='agent.get_full_name', read_only=True
    )

    class Meta:
        model = Deal
        fields = [
            'id', 'stage', 'stage_display',
            'property', 'property_info',
            'seller_contact', 'buyer_contact', 'buyer_name',
            'agent', 'agent_name',
            'price_agreed', 'commission_total',
            'deposit_amount', 'deposit_date',
            'contract_date', 'close_date',
            'notes', 'created_at', 'updated_at',
        ]

    def get_property_info(self, obj):
        if obj.property:
            return {
                'id': str(obj.property.pk),
                'title': str(obj.property),
                'city': obj.property.city,
                'price': str(obj.property.price),
            }
        return None

    def create(self, validated_data):
        request = self.context['request']
        validated_data['agency'] = request.user.agency
        validated_data['agent'] = request.user
        return super().create(validated_data)