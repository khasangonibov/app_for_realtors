"""
Celery задачи для отправки уведомлений.

Запуск вручную из консоли:
    from apps.notifications.tasks import send_overdue_tasks_notifications
    send_overdue_tasks_notifications.delay()
"""

from celery import shared_task
from django.utils import timezone


@shared_task(name='notifications.send_new_task_email')
def send_new_task_email(task_id):
    """Отправить уведомление о новой задаче.
    Вызывается автоматически после создания задачи.
    """
    from apps.tasks.models import Task
    from .email import notify_new_task

    try:
        task = Task.objects.select_related('agent', 'contact').get(pk=task_id)
        notify_new_task(task)
    except Task.DoesNotExist:
        pass


@shared_task(name='notifications.send_overdue_tasks_notifications')
def send_overdue_tasks_notifications():
    """Ежедневная рассылка о просроченных задачах.
    Запускается каждое утро в 9:00 по расписанию.
    """
    from apps.tasks.models import Task
    from apps.accounts.models import User
    from .email import notify_overdue_tasks

    now = timezone.now()

    # Находим всех агентов с просроченными задачами
    agents_with_overdue = User.objects.filter(
        tasks__is_done=False,
        tasks__due_date__lt=now,
        is_active=True,
    ).distinct()

    for agent in agents_with_overdue:
        overdue_tasks = list(
            Task.objects.filter(
                agent=agent,
                is_done=False,
                due_date__lt=now,
            ).select_related('contact').order_by('due_date')
        )
        if overdue_tasks:
            notify_overdue_tasks(agent, overdue_tasks)

    return f'Отправлено уведомлений: {agents_with_overdue.count()}'


@shared_task(name='notifications.send_selection_reaction_email')
def send_selection_reaction_email(selection_id, item_id):
    """Уведомление риелтору о реакции клиента в подборке."""
    from apps.selections.models import Selection, SelectionItem
    from .email import notify_selection_reaction

    try:
        selection = Selection.objects.select_related(
            'agent', 'contact'
        ).get(pk=selection_id)
        item = SelectionItem.objects.select_related('property').get(pk=item_id)
        notify_selection_reaction(selection, item)
    except (Selection.DoesNotExist, SelectionItem.DoesNotExist):
        pass


@shared_task(name='notifications.send_new_deal_email')
def send_new_deal_email(deal_id):
    """Уведомление менеджерам о новой сделке."""
    from apps.deals.models import Deal
    from .email import notify_new_deal

    try:
        deal = Deal.objects.select_related(
            'agency', 'agent', 'property', 'buyer_contact'
        ).get(pk=deal_id)
        notify_new_deal(deal)
    except Deal.DoesNotExist:
        pass