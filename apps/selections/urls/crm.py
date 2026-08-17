from django.urls import path
from apps.selections.views import crm as views

app_name = 'selections'

urlpatterns = [
    path('selections/', views.selection_list, name='list'),
    path('selections/create/', views.selection_create, name='create'),
    path('selections/<uuid:pk>/', views.selection_detail, name='detail'),
    path('selections/<uuid:pk>/items/<uuid:item_pk>/delete/', views.selection_item_delete, name='item_delete'),
    path('selections/<uuid:pk>/send-email/', views.selection_send_email, name='send_email'),
    path('selections/<uuid:pk>/delete/', views.selection_delete, name='delete'),
]