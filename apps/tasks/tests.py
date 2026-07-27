import pytest
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from apps.tasks.models import Task


@pytest.fixture
def overdue_task(db, agency, agent_user):
    """Просроченная задача."""
    return Task.objects.create(
        agency=agency, agent=agent_user,
        title='Просроченная задача',
        due_date=timezone.now() - timedelta(days=1),
        is_done=False,
    )


@pytest.fixture
def future_task(db, agency, agent_user):
    """Задача с будущим сроком."""
    return Task.objects.create(
        agency=agency, agent=agent_user,
        title='Будущая задача',
        due_date=timezone.now() + timedelta(days=3),
        is_done=False,
    )


@pytest.mark.django_db
class TestTaskModel:

    def test_is_overdue_true_for_past_due_date(self, overdue_task):
        assert overdue_task.is_overdue is True

    def test_is_overdue_false_for_future_due_date(self, future_task):
        assert future_task.is_overdue is False

    def test_is_overdue_false_when_done_even_if_past(self, db, agency, agent_user):
        """Выполненная задача не должна считаться просроченной,
        даже если срок уже прошёл.
        """
        task = Task.objects.create(
            agency=agency, agent=agent_user,
            title='Выполненная просроченная',
            due_date=timezone.now() - timedelta(days=5),
            is_done=True,
        )
        assert task.is_overdue is False


@pytest.mark.django_db
class TestTaskList:

    def test_overdue_and_future_separated_correctly(self, client, agent_user, overdue_task, future_task):
        """Список задач должен корректно разделять просроченные и активные."""
        client.force_login(agent_user)
        response = client.get(reverse('tasks:list'))
        assert overdue_task in response.context['overdue']
        assert overdue_task not in response.context['active']
        assert future_task in response.context['active']
        assert future_task not in response.context['overdue']

    def test_task_list_requires_login(self, client):
        response = client.get(reverse('tasks:list'))
        assert response.status_code == 302


@pytest.mark.django_db
class TestTaskDone:

    def test_marking_task_done_sets_timestamp(self, client, agent_user, future_task):
        """Отметка задачи выполненной должна проставлять done_at."""
        client.force_login(agent_user)
        assert future_task.done_at is None

        response = client.post(reverse('tasks:done', kwargs={'pk': future_task.pk}))
        assert response.status_code == 302

        future_task.refresh_from_db()
        assert future_task.is_done is True
        assert future_task.done_at is not None

    def test_done_only_accepts_post(self, client, agent_user, future_task):
        """GET-запрос к /done/ не должен выполнять действие —
        защита от CSRF через случайный переход по ссылке.
        """
        client.force_login(agent_user)
        client.get(reverse('tasks:done', kwargs={'pk': future_task.pk}))
        future_task.refresh_from_db()
        assert future_task.is_done is False
        