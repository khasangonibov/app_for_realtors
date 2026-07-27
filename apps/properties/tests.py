import pytest
from decimal import Decimal
from django.urls import reverse
from apps.properties.models import Property, PropertyPhoto
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

@pytest.fixture
def property_obj(db, agency, agent_user):
    """Тестовый объект недвижимости."""
    return Property.objects.create(
        agency=agency,
        agent=agent_user,
        deal_type=Property.DealType.SALE,
        property_type=Property.PropertyType.APARTMENT,
        price=Decimal('5000000'),
        area_total=Decimal('60.5'),
        rooms_count=2,
        city='Москва',
        street='ул. Тестовая',
        is_published=True,
        status='active',
    )


@pytest.mark.django_db
class TestPropertyModel:

    def test_price_per_sqm_calculation(self, property_obj):
        """Цена за м² должна вычисляться корректно."""
        expected = round(Decimal('5000000') / Decimal('60.5'), 2)
        assert property_obj.price_per_sqm == expected

    def test_price_per_sqm_none_without_area(self, db, agency, agent_user):
        """Без указанной площади price_per_sqm должен быть None,
        а не вызывать деление на ноль.
        """
        prop = Property.objects.create(
            agency=agency, agent=agent_user,
            price=Decimal('1000000'), city='Москва',
        )
        assert prop.price_per_sqm is None

    def test_cover_photo_returns_marked_photo(self, property_obj):
        """cover_photo должно возвращать фото с is_cover=True,
        даже если оно не первое по порядку.
        """
        PropertyPhoto.objects.create(
            property=property_obj, image='test1.jpg', order=0, is_cover=False,
        )
        cover = PropertyPhoto.objects.create(
            property=property_obj, image='test2.jpg', order=1, is_cover=True,
        )
        assert property_obj.cover_photo == cover

    def test_only_one_cover_photo_allowed(self, property_obj):
        """При сохранении нового is_cover=True старая обложка должна сняться."""
        photo1 = PropertyPhoto.objects.create(
            property=property_obj, image='test1.jpg', is_cover=True,
        )
        photo2 = PropertyPhoto.objects.create(
            property=property_obj, image='test2.jpg', is_cover=True,
        )
        photo1.refresh_from_db()
        assert photo1.is_cover is False
        assert photo2.is_cover is True


@pytest.mark.django_db
class TestPublicPropertyView:

    def test_published_property_is_accessible(self, client, property_obj):
        """Опубликованный объект должен открываться без авторизации."""
        url = property_obj.get_public_url()
        response = client.get(url)
        assert response.status_code == 200

    def test_unpublished_property_returns_404(self, client, property_obj):
        """Неопубликованный объект должен возвращать 404,
        даже если знать точный ID и токен.
        """
        property_obj.is_published = False
        property_obj.save()
        url = property_obj.get_public_url()
        response = client.get(url)
        assert response.status_code == 404

    def test_wrong_token_returns_404(self, client, property_obj):
        """Неверный токен в URL должен возвращать 404 —
        защита от подбора ссылок (IDOR).
        """
        url = property_obj.get_public_url()
        wrong_url = url.replace(str(property_obj.public_token), '00000000-0000-0000-0000-000000000000')
        response = client.get(wrong_url)
        assert response.status_code == 404

    def test_view_creates_propertyview_record(self, client, property_obj):
        """Просмотр публичной карточки должен фиксироваться для статистики."""
        from apps.properties.models import PropertyView
        assert PropertyView.objects.count() == 0
        client.get(property_obj.get_public_url())
        assert PropertyView.objects.filter(property=property_obj).count() == 1


@pytest.mark.django_db
class TestPropertyListAccess:

    def test_agent_sees_only_own_properties(self, client, agency, agent_user):
        """Риелтор должен видеть в списке только свои объекты,
        не объекты других риелторов агентства.
        """
        from apps.accounts.models import User, UserProfile

        other_agent = User.objects.create_user(
            username='other_agent', password='test', agency=agency,
        )
        UserProfile.objects.create(user=other_agent, role=UserProfile.Role.AGENT)

        Property.objects.create(
            agency=agency, agent=agent_user,
            price=Decimal('1000000'), city='Москва', title='Мой объект',
        )
        Property.objects.create(
            agency=agency, agent=other_agent,
            price=Decimal('2000000'), city='Москва', title='Чужой объект',
        )

        client.force_login(agent_user)
        response = client.get(reverse('properties:list'))
        properties = response.context['properties']

        titles = [p.title for p in properties]
        assert 'Мой объект' in titles
        assert 'Чужой объект' not in titles

    def test_manager_sees_all_agency_properties(self, client, agency, manager_user, agent_user):
        """Руководитель должен видеть все объекты агентства."""
        Property.objects.create(
            agency=agency, agent=agent_user,
            price=Decimal('1000000'), city='Москва', title='Объект риелтора',
        )
        client.force_login(manager_user)
        response = client.get(reverse('properties:list'))
        titles = [p.title for p in response.context['properties']]
        assert 'Объект риелтора' in titles
        


@pytest.fixture
def api_client(agent_user):
    """DRF APIClient с JWT-токеном авторизованного риелтора."""
    client = APIClient()
    refresh = RefreshToken.for_user(agent_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.mark.django_db
class TestPropertyAPI:

    def test_list_requires_authentication(self):
        client = APIClient()
        response = client.get('/api/v1/properties/')
        assert response.status_code == 401

    def test_list_returns_only_own_properties_for_agent(self, api_client, agency, agent_user):
        """API должно применять то же ограничение — риелтор видит только свои."""
        from apps.accounts.models import User, UserProfile

        other_agent = User.objects.create_user(
            username='api_other_agent', password='test', agency=agency,
        )
        UserProfile.objects.create(user=other_agent, role=UserProfile.Role.AGENT)

        Property.objects.create(
            agency=agency, agent=agent_user, price=Decimal('1000000'), city='Москва',
        )
        Property.objects.create(
            agency=agency, agent=other_agent, price=Decimal('2000000'), city='Москва',
        )

        response = api_client.get('/api/v1/properties/')
        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_create_property_via_api(self, api_client, agency, agent_user):
        """Создание объекта через API должно проставлять agency/agent автоматически."""
        response = api_client.post('/api/v1/properties/', {
            'deal_type': 'sale',
            'property_type': 'apartment',
            'status': 'active',
            'price': '4500000',
            'city': 'Казань',
        })
        assert response.status_code == 201
        prop = Property.objects.get(city='Казань')
        assert prop.agency == agency
        assert prop.agent == agent_user

    def test_public_endpoint_requires_no_auth(self, property_obj):
        """Публичный endpoint объекта должен работать без токена."""
        client = APIClient()
        url = f'/api/v1/properties/public/{property_obj.public_token}/'
        response = client.get(url)
        assert response.status_code == 200

    def test_public_endpoint_hides_unpublished(self, property_obj):
        """Неопубликованный объект не должен быть доступен даже с верным токеном."""
        property_obj.is_published = False
        property_obj.save()
        client = APIClient()
        url = f'/api/v1/properties/public/{property_obj.public_token}/'
        response = client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestAuthAPI:

    def test_obtain_token_with_valid_credentials(self, agent_user):
        client = APIClient()
        response = client.post('/api/v1/auth/token/', {
            'username': 'test_agent',
            'password': 'testpass123',
        })
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_obtain_token_fails_with_wrong_password(self, agent_user):
        client = APIClient()
        response = client.post('/api/v1/auth/token/', {
            'username': 'test_agent',
            'password': 'wrongpassword',
        })
        assert response.status_code == 401

    def test_me_endpoint_returns_current_user(self, api_client, agent_user):
        response = api_client.get('/api/v1/auth/me/')
        assert response.status_code == 200
        assert response.data['username'] == 'test_agent'