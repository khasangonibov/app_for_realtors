from rest_framework import serializers
from .models import User, Agency, UserProfile


class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = ['id', 'name', 'slug', 'city', 'phone', 'email']


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)
    role_display = serializers.CharField(
        source='profile.get_role_display', read_only=True
    )
    agency = AgencySerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name', 'phone',
            'avatar', 'role', 'role_display', 'agency',
        ]


class MeSerializer(serializers.ModelSerializer):
    """Данные текущего пользователя — для /api/v1/auth/me/"""
    role = serializers.CharField(source='profile.role', read_only=True)
    agency = AgencySerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name', 'phone',
            'avatar', 'role', 'agency',
        ]