"""
URL-маршруты приложения accounts.
Подключаются в config/urls.py с префиксом /crm/
"""

from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CRMLoginView.as_view(), name='login'),
    path('logout/', views.CRMLogoutView.as_view(), name='logout'),
    path('', views.dashboard, name='dashboard'),  # /crm/ — главная страница
]