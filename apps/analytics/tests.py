import pytest
from decimal import Decimal
from django.urls import reverse
from apps.properties.models import Property
from apps.contacts.models import Contact
from apps.deals.models import Deal


@pytest.mark.django_db
class TestAnalyticsDashboard:

    def test_dashboard_requires_login(self, client):
        response = client.get(reverse('analytics:dashboard'))
        assert response.status_code == 302

    def test_dashboard_loads_for_manager(self, client, manager_user):
        client.force_login(manager_user)
        response = client.get(reverse('analytics:dashboard'))
        assert response.status_code == 200

    def test_properties_grouped_by_status(self, client, manager_user, agency, agent_user):
        """Аналитика должна корректно группировать объекты по статусам."""
        Property.objects.create(
            agency=agency, agent=agent_user, price=Decimal('1000000'),
            city='Москва', status='active',
        )
        Property.objects.create(
            agency=agency, agent=agent_user, price=Decimal('2000000'),
            city='Москва', status='active',
        )
        Property.objects.create(
            agency=agency, agent=agent_user, price=Decimal('3000000'),
            city='Москва', status='draft',
        )
        client.force_login(manager_user)
        response = client.get(reverse('analytics:dashboard'))

        by_status = {item['label']: item['count'] for item in response.context['properties_by_status']}
        assert by_status.get('Активный') == 2
        assert by_status.get('Черновик') == 1

    def test_closed_deals_sum_only_counts_closed(self, client, manager_user, agency, agent_user):
        """closed_deals_sum должен учитывать только сделки со статусом closed."""
        from django.utils import timezone

        Deal.objects.create(
            agency=agency, agent=agent_user,
            stage=Deal.Stage.CLOSED,
            price_agreed=Decimal('5000000'),
            close_date=timezone.now().date(),
        )
        Deal.objects.create(
            agency=agency, agent=agent_user,
            stage=Deal.Stage.NEGOTIATION,
            price_agreed=Decimal('9999999'),
        )
        client.force_login(manager_user)
        response = client.get(reverse('analytics:dashboard'))

        assert response.context['closed_deals_sum'] == Decimal('5000000')

    def test_agent_stats_only_shown_to_manager(self, client, agent_user):
        """Риелтору не должна показываться статистика по всем агентам."""
        client.force_login(agent_user)
        response = client.get(reverse('analytics:dashboard'))
        assert response.context['agents_stats'] is None

    def test_agent_stats_shown_to_manager(self, client, manager_user):
        client.force_login(manager_user)
        response = client.get(reverse('analytics:dashboard'))
        assert response.context['agents_stats'] is not None