from rest_framework import serializers
from .models import Property, PropertyPhoto, PropertyFeature


class PropertyPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyPhoto
        fields = ['id', 'image', 'is_cover', 'order']


class PropertyFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyFeature
        fields = ['id', 'key', 'value']


class PropertyListSerializer(serializers.ModelSerializer):
    """Краткое представление для списка объектов."""
    cover_photo = serializers.SerializerMethodField()
    deal_type_display = serializers.CharField(
        source='get_deal_type_display', read_only=True
    )
    property_type_display = serializers.CharField(
        source='get_property_type_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    price_per_sqm = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = Property
        fields = [
            'id', 'deal_type', 'deal_type_display',
            'property_type', 'property_type_display',
            'status', 'status_display',
            'title', 'price', 'price_currency', 'price_per_sqm',
            'area_total', 'rooms_count', 'floor', 'floors_total',
            'city', 'district', 'street', 'building',
            'is_published', 'is_exclusive',
            'cover_photo', 'created_at',
        ]

    def get_cover_photo(self, obj):
        photo = obj.cover_photo
        if photo:
            request = self.context.get('request')
            url = photo.image.url
            if request:
                url = request.build_absolute_uri(url)
            return url
        return None


class PropertyDetailSerializer(PropertyListSerializer):
    """Полное представление объекта."""
    photos = PropertyPhotoSerializer(many=True, read_only=True)
    features = PropertyFeatureSerializer(many=True, read_only=True)
    public_url = serializers.SerializerMethodField()
    agent_name = serializers.CharField(
        source='agent.get_full_name', read_only=True
    )
    agent_phone = serializers.CharField(
        source='agent.phone', read_only=True
    )

    class Meta(PropertyListSerializer.Meta):
        fields = PropertyListSerializer.Meta.fields + [
            'description', 'area_living', 'area_kitchen',
            'latitude', 'longitude',
            'commission_percent', 'commission_fixed',
            'public_token', 'public_url',
            'photos', 'features',
            'agent_name', 'agent_phone',
            'updated_at',
        ]

    def get_public_url(self, obj):
        request = self.context.get('request')
        if request and obj.is_published:
            return request.build_absolute_uri(obj.get_public_url())
        return None


class PropertyWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/редактирования объекта."""

    class Meta:
        model = Property
        fields = [
            'deal_type', 'property_type', 'status',
            'title', 'description',
            'price', 'price_currency',
            'area_total', 'area_living', 'area_kitchen',
            'rooms_count', 'floor', 'floors_total',
            'city', 'district', 'street', 'building', 'apartment',
            'latitude', 'longitude',
            'is_published', 'is_exclusive',
            'commission_percent', 'commission_fixed',
        ]

    def create(self, validated_data):
        request = self.context['request']
        validated_data['agency'] = request.user.agency
        validated_data['agent'] = request.user
        return super().create(validated_data)