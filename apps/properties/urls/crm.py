from django.urls import path
from apps.properties.views import crm as views

app_name = 'properties'

urlpatterns = [
    path('properties/', views.property_list, name='list'),
    path('properties/create/', views.property_create, name='create'),
    path('properties/<uuid:pk>/edit/', views.property_edit, name='edit'),
    path('properties/<uuid:pk>/photos/', views.photo_upload, name='photo_upload'),
    path('properties/<uuid:pk>/photos/<uuid:photo_pk>/delete/', views.photo_delete, name='photo_delete'),
    path('properties/<uuid:pk>/photos/<uuid:photo_pk>/cover/', views.photo_set_cover, name='photo_cover'),
    path('properties/export/', views.property_export_excel, name='export'),
]