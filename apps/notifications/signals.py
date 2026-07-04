"""
Django сигналы — автоматически запускают Celery задачи
при создании задач, сделок и реакций в подборках.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='tasks.Task')
def on_task_created(sender, instance, created, **kwargs):
    """При создании задачи — отправляем уведомление риелтору."""
    if created:
        from apps.notifications.tasks import send_new_task_email
        # delay() — запускает задачу асинхронно через Celery
        # countdown=5 — небольшая задержка чтобы транзакция точно завершилась
        send_new_task_email.apply_async(
            args=[str(instance.pk)],
            countdown=5,
        )


@receiver(post_save, sender='deals.Deal')
def on_deal_created(sender, instance, created, **kwargs):
    """При создании сделки — уведомляем руководителей."""
    if created:
        from apps.notifications.tasks import send_new_deal_email
        send_new_deal_email.apply_async(
            args=[str(instance.pk)],
            countdown=5,
        )


@receiver(post_save, sender='selections.SelectionItem')
def on_selection_item_updated(sender, instance, created, **kwargs):
    """При изменении реакции клиента — уведомляем риелтора."""
    # Отправляем только если это не новый объект (created=False)
    # и статус изменился на что-то кроме 'new'
    if not created and instance.client_status != 'new':
        from apps.notifications.tasks import send_selection_reaction_email
        send_selection_reaction_email.apply_async(
            args=[str(instance.selection.pk), str(instance.pk)],
            countdown=5,
        )