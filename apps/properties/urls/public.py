from django.urls import path
from apps.properties.views import public as views
from apps.accounts import views as account_views

app_name = 'public'

urlpatterns = [
    # Каталог
    path('', views.catalog, name='catalog'),

    # Карточка объекта
    path(
        'object/<slug:agency_slug>/<uuid:pk>/<uuid:token>/',
        views.property_detail,
        name='property_detail',
    ),

    # Регистрация и профиль клиента
    path('register/', account_views.client_register, name='register'),
    path('profile/', account_views.client_profile, name='profile'),
    path('login/', account_views.PublicLoginView.as_view(), name='public_login'),
]