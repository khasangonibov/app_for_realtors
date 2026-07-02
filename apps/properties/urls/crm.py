from django.urls import path
from apps.properties.views import crm as views

app_name = 'properties'

urlpatterns = [
    path('properties/', views.property_list, name='list'),
    path('properties/create/', views.property_create, name='create'),
    path('properties/<uuid:pk>/edit/', views.property_edit, name='edit'),
]