from django.urls import path
from . import views

app_name = 'deals'

urlpatterns = [
    path('deals/', views.deal_board, name='board'),
    path('deals/create/', views.deal_create, name='create'),
    path('deals/export/', views.deal_export_excel, name='export'),
    path('deals/<uuid:pk>/edit/', views.deal_edit, name='edit'),
    path('deals/<uuid:pk>/delete/', views.deal_delete, name='delete'),
]