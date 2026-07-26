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
    
    # Сравнение объектов
    path('compare/', views.compare, name='compare'),
    path('compare/add/<uuid:pk>/', views.compare_add, name='compare_add'),
    path('compare/remove/<uuid:pk>/', views.compare_remove, name='compare_remove'),
    path('compare/clear/', views.compare_clear, name='compare_clear'),
    
    # Чат 
    path('chat/', account_views.client_chat_list, name='client_chat_list'),
    path('chat/room/<uuid:room_pk>/', account_views.client_chat, name='client_chat_room'),
    path('chat/new/', account_views.client_chat, name='client_chat_new'),
    path('chat/new/<uuid:agent_pk>/', account_views.client_chat, name='client_chat_agent'),
    path('chat/room/<uuid:room_pk>/poll/', account_views.client_chat_poll, name='client_chat_poll'),
    ]