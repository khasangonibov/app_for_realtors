from rest_framework import generics, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Property
from .serializers import (
    PropertyListSerializer,
    PropertyDetailSerializer,
    PropertyWriteSerializer,
)


class AgencyFilterMixin:
    """Миксин — фильтрует queryset по агентству текущего пользователя."""

    def get_queryset(self):
        qs = Property.objects.filter(
            agency=self.request.user.agency,
            is_deleted=False, 
        ).select_related('agent').prefetch_related('photos', 'features')

        if self.request.user.is_agent:
            qs = qs.filter(agent=self.request.user)

        return qs


class PropertyListCreateView(AgencyFilterMixin, generics.ListCreateAPIView):
    """
    GET  /api/v1/properties/  — список объектов
    POST /api/v1/properties/  — создать объект
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'city', 'street', 'description']
    ordering_fields = ['created_at', 'price', 'area_total']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PropertyWriteSerializer
        return PropertyListSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # Фильтры через query params
        status = self.request.query_params.get('status')
        deal_type = self.request.query_params.get('deal_type')
        property_type = self.request.query_params.get('property_type')
        city = self.request.query_params.get('city')
        
        if status:
            qs = qs.filter(status=status)
        if deal_type:
            qs = qs.filter(deal_type=deal_type)
        if property_type:
            qs = qs.filter(property_type=property_type)
        if city:
            qs = qs.filter(city__icontains=city)

        return qs


class PropertyDetailView(AgencyFilterMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/properties/{id}/  — детали объекта
    PUT    /api/v1/properties/{id}/  — обновить объект
    PATCH  /api/v1/properties/{id}/  — частичное обновление
    DELETE /api/v1/properties/{id}/  — мягкое удаление объекта
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PropertyWriteSerializer
        return PropertyDetailSerializer

    def perform_destroy(self, instance):
        """Переопределяем стандартное hard delete DRF —
        используем soft_delete(), как и в остальной системе.
        """
        instance.soft_delete()

class PropertyPublicView(APIView):
    """
    GET /api/v1/properties/public/{token}/
    Публичная карточка объекта — без авторизации.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        property_obj = get_object_or_404(
            Property,
            public_token=token,
            is_published=True,
            is_deleted=False, 
        )
        serializer = PropertyDetailSerializer(
            property_obj,
            context={'request': request}
        )
        return Response(serializer.data)