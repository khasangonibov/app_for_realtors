from django.urls import path
from . import api_views

urlpatterns = [
    path('deals/', api_views.DealListCreateView.as_view()),
    path('deals/<uuid:pk>/', api_views.DealDetailView.as_view()),
]