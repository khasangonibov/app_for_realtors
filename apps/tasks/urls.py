from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('tasks/', views.task_list, name='list'),
    path('tasks/create/', views.task_create, name='create'),
    path('tasks/<uuid:pk>/edit/', views.task_edit, name='edit'),
    path('tasks/<uuid:pk>/done/', views.task_done, name='done'),
]