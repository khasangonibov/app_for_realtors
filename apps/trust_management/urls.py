from django.urls import path
from . import views

app_name = 'trust_management'

urlpatterns = [
    path('management/', views.contract_list, name='list'),
    path('management/create/', views.contract_create, name='create'),
    path('management/<uuid:pk>/', views.contract_detail, name='detail'),
    path('management/<uuid:pk>/edit/', views.contract_edit, name='edit'),
    path('management/<uuid:pk>/report/', views.contract_report, name='report'),
    path('management/<uuid:pk>/delete/', views.contract_delete, name='delete'),
    path('management/<uuid:pk>/transactions/<uuid:transaction_pk>/delete/',
         views.transaction_delete, name='transaction_delete'),
    path('management/<uuid:pk>/documents/<uuid:document_pk>/delete/',
         views.document_delete, name='document_delete'),
]