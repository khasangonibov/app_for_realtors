import pytest
from django.urls import reverse
from apps.selections.models import Selection, SelectionItem
from apps.properties.models import Property
from decimal import Decimal


@pytest.fixture
def selection_obj(db, agency, agent_user):
    return Selection.objects.create(
        agency=agency, agent=agent_user, title='Подборка для теста',
    )


@pytest.fixture
def published_property(db, agency, agent_user):
    return Property.objects.create(
        agency=agency, agent=agent_user,
        price=Decimal('3000000'), city='Москва',
        is_published=True, status='active',
    )


@pytest.mark.django_db
class TestSelectionModel:

    def test_get_public_url_uses_token(self, selection_obj):
        url = selection_obj.get_public_url()
        assert str(selection_obj.public_token) in url


@pytest.mark.django_db
class TestSelectionItemReaction:

    def test_client_can_react_without_login(self, client, selection_obj, published_property):
        """Клиент должен иметь возможность поставить реакцию на объект
        в публичной подборке без авторизации.
        """
        item = SelectionItem.objects.create(
            selection=selection_obj, property=published_property,
        )
        url = reverse('selection_public:react', kwargs={
            'token': selection_obj.public_token, 'item_pk': item.pk,
        })
        response = client.post(url, {'status': 'liked'})
        assert response.status_code == 302

        item.refresh_from_db()
        assert item.client_status == SelectionItem.ClientStatus.LIKED

    def test_invalid_status_value_ignored(self, client, selection_obj, published_property):
        """Некорректное значение статуса не должно записываться в базу."""
        item = SelectionItem.objects.create(
            selection=selection_obj, property=published_property,
        )
        url = reverse('selection_public:react', kwargs={
            'token': selection_obj.public_token, 'item_pk': item.pk,
        })
        client.post(url, {'status': 'hacked_value'})

        item.refresh_from_db()
        assert item.client_status == SelectionItem.ClientStatus.NEW

    def test_public_selection_page_shows_items(self, client, selection_obj, published_property):
        """Публичная страница подборки должна показывать добавленные объекты."""
        SelectionItem.objects.create(
            selection=selection_obj, property=published_property,
        )
        url = reverse('selection_public:detail', kwargs={'token': selection_obj.public_token})
        response = client.get(url)
        assert response.status_code == 200
        assert published_property in [item.property for item in response.context['items']]


@pytest.mark.django_db
class TestSelectionItemDuplicate:

    def test_cannot_add_same_property_twice(self, db, selection_obj, published_property):
        """unique_together должен предотвращать дублирование
        одного объекта в одной подборке.
        """
        from django.db import IntegrityError

        SelectionItem.objects.create(
            selection=selection_obj, property=published_property,
        )
        with pytest.raises(IntegrityError):
            SelectionItem.objects.create(
                selection=selection_obj, property=published_property,
            )
            