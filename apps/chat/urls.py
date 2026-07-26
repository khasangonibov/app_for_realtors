from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Чаты с клиентами
    path('chat/', views.agent_chat_list, name='agent_list'),
    path('chat/<uuid:pk>/', views.agent_chat_room, name='agent_room'),
    path('chat/<uuid:pk>/poll/', views.agent_chat_poll, name='agent_poll'),
    path('chat/<uuid:pk>/claim/', views.agent_claim_room, name='agent_claim'),

    # Внутренние чаты сотрудников
    path('internal-chat/', views.internal_chat_list, name='internal_list'),
    path('internal-chat/start/<uuid:user_pk>/', views.internal_chat_start, name='internal_start'),
    path('internal-chat/group/create/', views.internal_chat_create_group, name='internal_create_group'),
    path('internal-chat/<uuid:pk>/', views.internal_chat_room, name='internal_room'),
    path('internal-chat/<uuid:pk>/poll/', views.internal_chat_poll, name='internal_poll'),
]