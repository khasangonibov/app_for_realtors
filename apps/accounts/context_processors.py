from django.utils import timezone
from django.db.models import Q as models_Q



def agency_context(request):
    """Добавляет переменную `agency` в контекст шаблона.

    Если пользователь авторизован и у него есть agency — отдаём его.
    Если нет (например, анонимный пользователь на публичной странице) —
    отдаём None, и в шаблоне можно проверить через {% if agency %}.
    """
    agency = None
    overdue_tasks_count = 0
    unread_chats_count = 0
    unread_internal_count = 0

    if request.user.is_authenticated and hasattr(request.user, 'agency'):
        agency = request.user.agency

        if agency and request.user.role != 'client':
            from apps.tasks.models import Task
            overdue_tasks_count = Task.objects.filter(
                agency=agency,
                agent=request.user,
                is_done=False,
                due_date__lt=timezone.now(),
            ).count()

            from apps.chat.models import ChatRoom, InternalChat

            if request.user.is_agent:
                chat_rooms = ChatRoom.objects.filter(
                    agency=agency,
                ).filter(
                    models_Q(agent=request.user) |
                    models_Q(agent=None)
                )
            else:
                chat_rooms = ChatRoom.objects.filter(agency=agency)

            for room in chat_rooms:
                unread_chats_count += room.messages.filter(
                    is_read=False,
                ).exclude(sender=request.user).count()

            # Непрочитанные внутренние чаты
            internal_chats = InternalChat.objects.filter(
                agency=agency,
                participants=request.user,
            )
            for chat in internal_chats:
                unread_internal_count += chat.messages.exclude(
                    sender=request.user,
                ).exclude(
                    read_by__user=request.user,
                ).count()

    return {
        'agency': agency,
        'overdue_tasks_count': overdue_tasks_count,
        'unread_chats_count': unread_chats_count,
        'unread_internal_count': unread_internal_count,
    }