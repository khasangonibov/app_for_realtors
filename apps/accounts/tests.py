import pytest
from django.urls import reverse
from apps.accounts.models import User, UserProfile, Agency


@pytest.mark.django_db
class TestUserModel:

    def test_user_role_property(self, agent_user):
        """Проверяем что свойство role корректно читает из UserProfile."""
        assert agent_user.role == UserProfile.Role.AGENT
        assert agent_user.is_agent is True
        assert agent_user.is_manager is False

    def test_user_without_profile_has_no_role(self, db, agency):
        """Пользователь без UserProfile должен возвращать role=None,
        а не падать с ошибкой.
        """
        user = User.objects.create_user(
            username='no_profile', password='test', agency=agency,
        )
        assert user.role is None


@pytest.mark.django_db
class TestCRMLogin:

    def test_login_page_loads(self, client):
        """Страница логина должна открываться без ошибок."""
        response = client.get(reverse('accounts:login'))
        assert response.status_code == 200

    def test_agent_can_login(self, client, agent_user):
        """Риелтор должен успешно авторизоваться и попасть на дашборд."""
        response = client.post(reverse('accounts:login'), {
            'username': 'test_agent',
            'password': 'testpass123',
        })
        assert response.status_code == 302
        assert response.url == '/crm/'

    def test_client_cannot_login_to_crm(self, client, client_user):
        """Клиент (роль CLIENT) не должен иметь доступ к CRM-логину."""
        response = client.post(reverse('accounts:login'), {
            'username': 'test_client',
            'password': 'testpass123',
        })
        # Форма должна вернуть ошибку, а не редирект
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated

    def test_wrong_password_shows_error(self, client, agent_user):
        """Неверный пароль должен показывать форму с ошибкой."""
        response = client.post(reverse('accounts:login'), {
            'username': 'test_agent',
            'password': 'wrongpassword',
        })
        assert response.status_code == 200
        assert response.context['form'].errors


@pytest.mark.django_db
class TestDashboardAccess:

    def test_dashboard_requires_login(self, client):
        """Неавторизованный пользователь должен быть перенаправлен на логин."""
        response = client.get(reverse('accounts:dashboard'))
        assert response.status_code == 302

    def test_agent_can_access_dashboard(self, authenticated_client):
        """Авторизованный риелтор должен видеть дашборд."""
        response = authenticated_client.get(reverse('accounts:dashboard'))
        assert response.status_code == 200

    def test_client_cannot_access_crm_dashboard(self, client, client_user):
        """Клиент не должен иметь доступ к CRM-дашборду даже если залогинен."""
        client.force_login(client_user)
        response = client.get(reverse('accounts:dashboard'))
        # Должен быть редирект (crm_required декоратор блокирует)
        assert response.status_code == 302