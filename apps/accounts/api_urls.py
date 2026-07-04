from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import api_views

urlpatterns = [
    # Получить JWT токен (логин)
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain'),
    # Обновить токен
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Данные текущего пользователя
    path('auth/me/', api_views.MeView.as_view(), name='api_me'),
]