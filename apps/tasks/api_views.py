from rest_framework import generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Task
from .serializers import TaskSerializer


class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Task.objects.filter(
            agency=self.request.user.agency,
            agent=self.request.user,
        )
        is_done = self.request.query_params.get('is_done')
        if is_done is not None:
            qs = qs.filter(is_done=is_done.lower() == 'true')
        return qs


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(
            agency=self.request.user.agency,
            agent=self.request.user,
        )


class TaskDoneView(generics.UpdateAPIView):
    """PATCH /api/v1/tasks/{id}/done/ — отметить задачу выполненной."""
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(
            agency=self.request.user.agency,
            agent=self.request.user,
        )

    def patch(self, request, *args, **kwargs):
        task = self.get_object()
        task.is_done = True
        task.done_at = timezone.now()
        task.save(update_fields=['is_done', 'done_at'])
        return Response(TaskSerializer(task).data)