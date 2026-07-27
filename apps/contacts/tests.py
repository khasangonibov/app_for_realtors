import pytest
from django.urls import reverse
from apps.contacts.models import Contact, ContactActivity


@pytest.fixture
def contact_obj(db, agency, agent_user):
    """Тестовый контакт."""
    return Contact.objects.create(
        agency=agency,
        agent=agent_user,
        first_name='Мария',
        last_name='Клиентова',
        phone='+7 (900) 123-45-67',
        email='maria@test.com',
        contact_type=Contact.ContactType.BUYER,
        status=Contact.Status.NEW,
    )


@pytest.mark.django_db
class TestContactModel:

    def test_full_name_property(self, contact_obj):
        """full_name должен склеивать фамилию, имя, отчество."""
        assert contact_obj.full_name == 'Клиентова Мария'

    def test_full_name_falls_back_to_phone(self, db, agency, agent_user):
        """Если имя/фамилия не указаны — full_name должен вернуть телефон,
        чтобы контакт не отображался пустой строкой.
        """
        contact = Contact.objects.create(
            agency=agency, agent=agent_user,
            first_name='', phone='+79991234567',
        )
        assert contact.full_name == '+79991234567'


@pytest.mark.django_db
class TestContactListAccess:

    def test_agent_sees_only_own_contacts(self, client, agency, agent_user):
        """Риелтор видит только своих контактов."""
        from apps.accounts.models import User, UserProfile

        other_agent = User.objects.create_user(
            username='other_agent2', password='test', agency=agency,
        )
        UserProfile.objects.create(user=other_agent, role=UserProfile.Role.AGENT)

        Contact.objects.create(
            agency=agency, agent=agent_user,
            first_name='Мой', phone='+70001112233',
        )
        Contact.objects.create(
            agency=agency, agent=other_agent,
            first_name='Чужой', phone='+70009998877',
        )

        client.force_login(agent_user)
        response = client.get(reverse('contacts:list'))
        names = [c.first_name for c in response.context['contacts']]

        assert 'Мой' in names
        assert 'Чужой' not in names

    def test_contact_list_requires_login(self, client):
        response = client.get(reverse('contacts:list'))
        assert response.status_code == 302


@pytest.mark.django_db
class TestContactActivity:

    def test_add_activity_to_contact(self, client, agent_user, contact_obj):
        """Добавление активности через форму на странице контакта."""
        client.force_login(agent_user)
        response = client.post(
            reverse('contacts:detail', kwargs={'pk': contact_obj.pk}),
            {
                'activity_type': ContactActivity.ActivityType.CALL,
                'description': 'Позвонил, обсудили детали.',
            },
        )
        assert response.status_code == 302
        assert ContactActivity.objects.filter(contact=contact_obj).count() == 1

    def test_activity_records_agent(self, client, agent_user, contact_obj):
        """Активность должна фиксировать текущего пользователя как агента."""
        client.force_login(agent_user)
        client.post(
            reverse('contacts:detail', kwargs={'pk': contact_obj.pk}),
            {
                'activity_type': ContactActivity.ActivityType.NOTE,
                'description': 'Заметка.',
            },
        )
        activity = ContactActivity.objects.get(contact=contact_obj)
        assert activity.agent == agent_user


@pytest.mark.django_db
class TestContactCreateEdit:

    def test_create_contact(self, client, agent_user, agency):
        """Создание контакта должно привязывать agency и agent автоматически."""
        client.force_login(agent_user)
        response = client.post(reverse('contacts:create'), {
            'first_name': 'Новый',
            'last_name': 'Контакт',
            'phone': '+79995554433',
            'contact_type': Contact.ContactType.BUYER,
            'status': Contact.Status.NEW,
            'source': Contact.Source.CALL,
        })
        assert response.status_code == 302
        contact = Contact.objects.get(first_name='Новый')
        assert contact.agency == agency
        assert contact.agent == agent_user

    def test_agent_cannot_edit_foreign_agency_contact(self, client, agent_user, db):
        """Риелтор не должен иметь доступ к контакту чужого агентства."""
        from apps.accounts.models import Agency
        other_agency = Agency.objects.create(name='Другое агентство', slug='other-agency')
        foreign_contact = Contact.objects.create(
            agency=other_agency, first_name='Чужой', phone='+70001112233',
        )
        client.force_login(agent_user)
        response = client.get(reverse('contacts:edit', kwargs={'pk': foreign_contact.pk}))
        assert response.status_code == 404