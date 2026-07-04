from django.urls import path
from . import api_views

urlpatterns = [
    path('tasks/', api_views.TaskListCreateView.as_view()),
    path('tasks/<uuid:pk>/', api_views.TaskDetailView.as_view()),
    path('tasks/<uuid:pk>/done/', api_views.TaskDoneView.as_view()),
]