"""
URL-маршруты приложения accounts.
Подключаются в config/urls.py с префиксом /crm/
"""

from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  
    path('users/', views.users_list, name='users_list'),
    path('users/invite/', views.user_invite, name='user_invite'),
    path('users/<uuid:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<uuid:pk>/toggle/', views.user_toggle_active, name='user_toggle'),
    path('users/<uuid:pk>/reset-password/', views.user_reset_password, name='user_reset_password'),
] 