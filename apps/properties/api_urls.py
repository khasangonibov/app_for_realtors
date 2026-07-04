from django.urls import path
from . import api_views

urlpatterns = [
    path('properties/', api_views.PropertyListCreateView.as_view()),
    path('properties/<uuid:pk>/', api_views.PropertyDetailView.as_view()),
    path('properties/public/<uuid:token>/', api_views.PropertyPublicView.as_view()),
]