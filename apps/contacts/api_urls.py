from django.urls import path
from . import api_views

urlpatterns = [
    path('contacts/', api_views.ContactListCreateView.as_view()),
    path('contacts/<uuid:pk>/', api_views.ContactDetailView.as_view()),
]