"""
Функции отправки email-уведомлений.
Используют Django шаблоны для HTML писем.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_html_email(subject, template_name, context, to_email):
    """Базовая функция отправки HTML письма.

    subject       — тема письма
    template_name — путь к HTML шаблону
    context       — данные для шаблона
    to_email      — адрес получателя (строка или список)
    """
    if isinstance(to_email, str):
        to_email = [to_email]

    # Рендерим HTML из шаблона
    html_content = render_to_string(template_name, context)

    # Текстовая версия — просто тема + базовый текст
    # (для почтовых клиентов без HTML)
    text_content = f"{subject}\n\nОткройте письмо в HTML-совместимом клиенте."

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to_email,
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def notify_new_task(task):
    """Уведомление риелтору о новой задаче."""
    if not task.agent.email:
        return

    send_html_email(
        subject=f'Новая задача: {task.title}',
        template_name='notifications/email/new_task.html',
        context={'task': task},
        to_email=task.agent.email,
    )


def notify_overdue_tasks(agent, tasks):
    """Уведомление риелтору о просроченных задачах."""
    if not agent.email or not tasks:
        return

    send_html_email(
        subject=f'Просроченные задачи ({len(tasks)} шт.)',
        template_name='notifications/email/overdue_tasks.html',
        context={'agent': agent, 'tasks': tasks},
        to_email=agent.email,
    )


def notify_selection_reaction(selection, item):
    """Уведомление риелтору когда клиент оставил реакцию в подборке."""
    if not selection.agent or not selection.agent.email:
        return

    send_html_email(
        subject=f'Клиент оценил объект в подборке «{selection.title}»',
        template_name='notifications/email/selection_reaction.html',
        context={
            'selection': selection,
            'item': item,
            'contact': selection.contact,
        },
        to_email=selection.agent.email,
    )


def notify_new_deal(deal):
    """Уведомление руководителю агентства о новой сделке."""
    from apps.accounts.models import User, UserProfile

    # Находим всех менеджеров и администраторов агентства
    managers = User.objects.filter(
        agency=deal.agency,
        profile__role__in=[
            UserProfile.Role.MANAGER,
            UserProfile.Role.ADMIN,
        ],
        is_active=True,
    ).exclude(email='')

    for manager in managers:
        send_html_email(
            subject=f'Новая сделка в агентстве',
            template_name='notifications/email/new_deal.html',
            context={'deal': deal, 'manager': manager},
            to_email=manager.email,
        )