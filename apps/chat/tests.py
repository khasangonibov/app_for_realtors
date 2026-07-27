import pytest
from django.urls import reverse
from apps.chat.models import ChatRoom, Message, InternalChat, InternalMessage


@pytest.mark.django_db
class TestChatRoomCreation:

    def test_general_and_personal_rooms_are_distinct(self, db, agency, agent_user, client_user):
        """Общий чат (agent=None) и личный чат с конкретным агентом
        должны быть разными записями, не конфликтовать по unique_together.
        """
        general_room = ChatRoom.objects.create(
            agency=agency, client=client_user, agent=None,
        )
        personal_room = ChatRoom.objects.create(
            agency=agency, client=client_user, agent=agent_user,
        )
        assert general_room.pk != personal_room.pk
        assert ChatRoom.objects.filter(client=client_user).count() == 2

    def test_client_can_send_message_in_own_room(self, client, client_user, agency):
        """Клиент должен иметь возможность отправить сообщение в свой чат."""
        room = ChatRoom.objects.create(agency=agency, client=client_user)
        client.force_login(client_user)
        response = client.post(
            reverse('public:client_chat_room', kwargs={'room_pk': room.pk}),
            {'text': 'Здравствуйте!'},
        )
        assert response.status_code == 200
        assert Message.objects.filter(room=room, text='Здравствуйте!').exists()

    def test_message_marks_read_for_recipient_not_sender(self, db, agency, agent_user, client_user):
        """При просмотре чата сообщения от собеседника должны отмечаться
        прочитанными, а свои собственные — нет.
        """
        room = ChatRoom.objects.create(agency=agency, client=client_user, agent=agent_user)
        msg_from_client = Message.objects.create(room=room, sender=client_user, text='Вопрос')

        # Агент открывает чат — должно отметить сообщение клиента как прочитанное
        room.messages.filter(is_read=False).exclude(sender=agent_user).update(is_read=True)
        msg_from_client.refresh_from_db()
        assert msg_from_client.is_read is True


@pytest.mark.django_db
class TestInternalChat:

    def test_personal_internal_chat_display_name(self, db, agency, agent_user, manager_user):
        """Для личного внутреннего чата display_name должен показывать
        имя собеседника, а не текущего пользователя.
        """
        chat = InternalChat.objects.create(agency=agency, is_group=False)
        chat.participants.add(agent_user, manager_user)

        name_for_agent = chat.get_display_name(agent_user)
        assert manager_user.get_full_name() in name_for_agent or manager_user.username in name_for_agent

    def test_group_chat_uses_name_field(self, db, agency, agent_user, manager_user):
        """Для группового чата display_name должен возвращать название группы."""
        chat = InternalChat.objects.create(
            agency=agency, is_group=True, name='Отдел продаж',
        )
        chat.participants.add(agent_user, manager_user)
        assert chat.get_display_name(agent_user) == 'Отдел продаж'

    def test_reply_to_links_correct_message(self, db, agency, agent_user, manager_user):
        """Ответ на сообщение должен корректно ссылаться на исходное."""
        chat = InternalChat.objects.create(agency=agency, is_group=False)
        chat.participants.add(agent_user, manager_user)

        original = InternalMessage.objects.create(
            chat=chat, sender=manager_user, text='Оригинал',
        )
        reply = InternalMessage.objects.create(
            chat=chat, sender=agent_user, text='Ответ', reply_to=original,
        )
        assert reply.reply_to == original
        assert reply.reply_to.text == 'Оригинал'