from django.urls import path
from apps.selections.views import public as views

app_name = 'selection_public'

urlpatterns = [
    path('selection/<uuid:token>/', views.selection_detail, name='detail'),
    path('selection/<uuid:token>/react/<uuid:item_pk>/',
         views.selection_item_react, name='react'),
]