from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    path('contacts/', views.contact_list, name='list'),
    path('contacts/create/', views.contact_create, name='create'),
    path('contacts/<uuid:pk>/', views.contact_detail, name='detail'),
    path('contacts/<uuid:pk>/edit/', views.contact_edit, name='edit'),
    path('contacts/export/', views.contact_export_excel, name='export'),
]