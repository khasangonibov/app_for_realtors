from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('chat/', views.chat_list, name='list'),  # ← новый единый список
    
    path('chat/clients/<uuid:pk>/', views.agent_chat_room, name='agent_room'),
    path('chat/clients/<uuid:pk>/poll/', views.agent_chat_poll, name='agent_poll'),
    path('chat/clients/<uuid:pk>/claim/', views.agent_claim_room, name='agent_claim'),
    path('chat/internal/start/<uuid:user_pk>/', views.internal_chat_start, name='internal_start'),
    path('chat/internal/group/create/', views.internal_chat_create_group, name='internal_create_group'),
    path('chat/internal/<uuid:pk>/', views.internal_chat_room, name='internal_room'),
    path('chat/internal/<uuid:pk>/poll/', views.internal_chat_poll, name='internal_poll'),
]