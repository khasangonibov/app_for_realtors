"""
Django сигналы — автоматически запускают Celery задачи
при создании задач, сделок и реакций в подборках.
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver


@receiver(pre_save, sender='tasks.Task')
def store_old_agent(sender, instance, **kwargs):
    """Перед сохранением запоминаем предыдущего исполнителя."""
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_agent_id = str(old.agent_id) if old.agent_id else None
        except sender.DoesNotExist:
            instance._old_agent_id = None
    else:
        instance._old_agent_id = None


@receiver(post_save, sender='tasks.Task')
def on_task_created(sender, instance, created, **kwargs):
    """Уведомляем исполнителя при создании задачи
    или при смене исполнителя на существующей.
    """
    from apps.notifications.tasks import send_new_task_email

    old_agent_id = getattr(instance, '_old_agent_id', None)
    new_agent_id = str(instance.agent_id) if instance.agent_id else None
    print(f'DEBUG: old={old_agent_id!r} new={new_agent_id!r} created={created}')
    should_notify = created or (old_agent_id != new_agent_id)

    if should_notify:
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