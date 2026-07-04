from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    task_type_display = serializers.CharField(
        source='get_task_type_display', read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display', read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description',
            'task_type', 'task_type_display',
            'priority', 'priority_display',
            'due_date', 'is_done', 'done_at', 'is_overdue',
            'contact', 'related_property',
            'created_at', 'updated_at',
        ]

    def create(self, validated_data):
        request = self.context['request']
        validated_data['agency'] = request.user.agency
        validated_data['agent'] = request.user
        return super().create(validated_data)