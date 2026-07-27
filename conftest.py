"""
Общие фикстуры для всех тестов.
conftest.py в корне проекта доступен во всех тестах автоматически,
без явного импорта.
"""

import pytest
from apps.accounts.models import Agency, User, UserProfile


@pytest.fixture
def agency(db):
    """Тестовое агентство."""
    return Agency.objects.create(
        name='Тестовое агентство',
        slug='test-agency-pytest',
        city='Москва',
    )


@pytest.fixture
def agent_user(db, agency):
    """Тестовый риелтор."""
    user = User.objects.create_user(
        username='test_agent',
        email='agent@test.com',
        password='testpass123',
        agency=agency,
        first_name='Иван',
        last_name='Риелторов',
    )
    UserProfile.objects.create(user=user, role=UserProfile.Role.AGENT)
    return user


@pytest.fixture
def manager_user(db, agency):
    """Тестовый руководитель."""
    user = User.objects.create_user(
        username='test_manager',
        email='manager@test.com',
        password='testpass123',
        agency=agency,
    )
    UserProfile.objects.create(user=user, role=UserProfile.Role.MANAGER)
    return user


@pytest.fixture
def client_user(db, agency):
    """Тестовый внешний пользователь (клиент)."""
    user = User.objects.create_user(
        username='test_client',
        email='client@test.com',
        password='testpass123',
    )
    UserProfile.objects.create(user=user, role=UserProfile.Role.CLIENT)
    return user


@pytest.fixture
def authenticated_client(client, agent_user):
    """Django test client, залогиненный под риелтором."""
    client.login(username='test_agent', password='testpass123')
    return client