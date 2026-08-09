"""
Сигналы приложения accounts.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Agency, User


@receiver(post_save, sender=Agency)
def attach_orphan_users_to_agency(sender, instance, created, **kwargs):
    """Когда создаётся первое (и единственное) агентство —
    автоматически привязываем к нему всех пользователей без агентства
    (например, суперпользователя, созданного через createsuperuser
    до появления записи Agency).
    """
    if created:
        User.objects.filter(agency__isnull=True).update(agency=instance)