import pytest
from decimal import Decimal
from django.urls import reverse
from apps.trust_management.models import ManagementContract, Transaction
from apps.properties.models import Property
from apps.contacts.models import Contact


@pytest.fixture
def managed_property(db, agency, agent_user):
    return Property.objects.create(
        agency=agency, agent=agent_user,
        price=Decimal('6000000'), city='Москва',
    )


@pytest.fixture
def owner_contact(db, agency, agent_user):
    return Contact.objects.create(
        agency=agency, agent=agent_user,
        first_name='Собственник', phone='+79997776655',
    )


@pytest.fixture
def contract_obj(db, agency, agent_user, managed_property, owner_contact):
    return ManagementContract.objects.create(
        agency=agency,
        related_property=managed_property,
        owner=owner_contact,
        agent=agent_user,
        start_date='2026-01-01',
        status=ManagementContract.Status.ACTIVE,
    )


@pytest.mark.django_db
class TestManagementContractFinancials:

    def test_net_income_calculation(self, contract_obj):
        """Чистый доход = доходы минус расходы."""
        Transaction.objects.create(
            contract=contract_obj, type=Transaction.Type.INCOME,
            category=Transaction.Category.RENT,
            amount=Decimal('50000'), date='2026-02-01',
        )
        Transaction.objects.create(
            contract=contract_obj, type=Transaction.Type.EXPENSE,
            category=Transaction.Category.UTILITIES,
            amount=Decimal('5000'), date='2026-02-05',
        )
        assert contract_obj.total_income == Decimal('50000')
        assert contract_obj.total_expense == Decimal('5000')
        assert contract_obj.net_income == Decimal('45000')

    def test_net_income_zero_without_transactions(self, contract_obj):
        """Без транзакций все суммы должны быть нулевыми, а не None
        (иначе арифметика в шаблонах сломается).
        """
        assert contract_obj.total_income == 0
        assert contract_obj.total_expense == 0
        assert contract_obj.net_income == 0


@pytest.mark.django_db
class TestManagementContractAccess:

    def test_one_property_cannot_have_two_contracts(self, db, contract_obj, managed_property, owner_contact, agency):
        """OneToOneField должен предотвращать создание второго договора
        на тот же объект.
        """
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            ManagementContract.objects.create(
                agency=agency, related_property=managed_property,
                owner=owner_contact, start_date='2026-03-01',
            )

    def test_agent_can_view_own_contract(self, client, agent_user, contract_obj):
        client.force_login(agent_user)
        response = client.get(reverse('trust_management:detail', kwargs={'pk': contract_obj.pk}))
        assert response.status_code == 200

    def test_add_transaction_logs_activity(self, client, agent_user, contract_obj):
        """Добавление транзакции должно создавать запись в журнале действий."""
        from apps.trust_management.models import ActivityLog

        client.force_login(agent_user)
        client.post(
            reverse('trust_management:detail', kwargs={'pk': contract_obj.pk}),
            {
                'add_transaction': '1',
                'type': Transaction.Type.INCOME,
                'category': Transaction.Category.RENT,
                'amount': '30000',
                'date': '2026-03-01',
                'description': 'Аренда за март',
            },
        )
        assert ActivityLog.objects.filter(contract=contract_obj).exists()