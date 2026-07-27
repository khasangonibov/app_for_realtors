import pytest
from decimal import Decimal
from django.urls import reverse
from apps.deals.models import Deal
from apps.contacts.models import Contact


@pytest.fixture
def buyer_contact(db, agency, agent_user):
    return Contact.objects.create(
        agency=agency, agent=agent_user,
        first_name='Покупатель', phone='+79990001122',
        contact_type=Contact.ContactType.BUYER,
    )


@pytest.fixture
def deal_obj(db, agency, agent_user, buyer_contact):
    return Deal.objects.create(
        agency=agency,
        agent=agent_user,
        buyer_contact=buyer_contact,
        stage=Deal.Stage.NEGOTIATION,
        price_agreed=Decimal('4500000'),
    )


@pytest.mark.django_db
class TestDealModel:

    def test_deal_str_includes_property_and_buyer(self, deal_obj, buyer_contact):
        """__str__ должен включать покупателя, если объект не привязан."""
        assert buyer_contact.full_name in str(deal_obj)


@pytest.mark.django_db
class TestDealBoard:

    def test_board_groups_deals_by_stage(self, client, agent_user, deal_obj):
        """Kanban-доска должна группировать сделки по стадиям."""
        client.force_login(agent_user)
        response = client.get(reverse('deals:board'))
        assert response.status_code == 200
        board = response.context['board']
        assert deal_obj in board['negotiation']['deals']

    def test_closed_deals_excluded_from_active_board(self, client, agent_user, agency, buyer_contact):
        """Закрытые сделки не должны попадать в активные колонки канбана."""
        closed_deal = Deal.objects.create(
            agency=agency, agent=agent_user,
            buyer_contact=buyer_contact,
            stage=Deal.Stage.CLOSED,
        )
        client.force_login(agent_user)
        response = client.get(reverse('deals:board'))
        for column in response.context['board'].values():
            assert closed_deal not in column['deals']
        assert closed_deal in response.context['finished']


@pytest.mark.django_db
class TestDealCreate:

    def test_create_deal_assigns_agency_and_agent(self, client, agent_user, agency, buyer_contact):
        """При создании сделки agency и agent должны проставляться автоматически."""
        client.force_login(agent_user)
        response = client.post(reverse('deals:create'), {
            'stage': Deal.Stage.NEGOTIATION,
            'buyer_contact': buyer_contact.pk,
            'price_agreed': '3000000',
        })
        assert response.status_code == 302
        deal = Deal.objects.filter(buyer_contact=buyer_contact).first()
        assert deal is not None
        assert deal.agency == agency
        assert deal.agent == agent_user