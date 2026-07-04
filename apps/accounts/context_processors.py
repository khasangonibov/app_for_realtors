from django.utils import timezone

"""
Context processor — автоматически добавляет данные агентства
в контекст всех шаблонов. Это удобно, например, для шапки сайта
или футера, где нужно показать название/логотип агентства
независимо от того, какая view рендерит страницу.
"""


def agency_context(request):
    """Добавляет переменную `agency` в контекст шаблона.

    Если пользователь авторизован и у него есть agency — отдаём его.
    Если нет (например, анонимный пользователь на публичной странице) —
    отдаём None, и в шаблоне можно проверить через {% if agency %}.
    """
    agency = None
    overdue_tasks_count = 0

    if request.user.is_authenticated and hasattr(request.user, 'agency'):
        agency = request.user.agency

        # Считаем просроченные задачи для бейджа в навбаре
        if agency and request.user.role != 'client':
            from apps.tasks.models import Task
            overdue_tasks_count = Task.objects.filter(
                agency=agency,
                agent=request.user,
                is_done=False,
                due_date__lt=timezone.now(),
            ).count()

    return {
        'agency': agency,
        'overdue_tasks_count': overdue_tasks_count,
    }