from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.db.models import Max

from .models import ChatRoom, Message, InternalChat, InternalMessage, InternalMessageRead
from apps.accounts.models import Agency, User
from apps.contacts.models import Contact
from apps.accounts.decorators import crm_required


def get_or_create_room(client, agency, agent=None):
    """Получить или создать комнату чата.
    agent=None означает общий чат без конкретного риелтора.
    """
    room, created = ChatRoom.objects.get_or_create(
        agency=agency,
        client=client,
        agent=agent,
    )

    if created and client.email:
        contact = Contact.objects.filter(
            email=client.email,
            agency=agency,
        ).first()
        if contact:
            room.contact = contact
            # Если агент не выбран — берём из контакта
            if not agent and contact.agent:
                room.agent = contact.agent
            room.save()

    return room


@login_required
def client_chat_list(request):
    """Список чатов клиента — выбор риелтора или общий чат."""
    agency = Agency.objects.first()
    if not agency:
        return render(request, 'chat/client_list.html', {'error': 'Агентство не найдено.'})

    # Получаем список риелторов агентства
    from apps.accounts.models import UserProfile
    agents = User.objects.filter(
        agency=agency,
        profile__role__in=[
            UserProfile.Role.AGENT,
            UserProfile.Role.MANAGER,
        ],
        is_active=True,
    ).select_related('profile')

    # Существующие чаты клиента
    existing_rooms = ChatRoom.objects.filter(
        agency=agency,
        client=request.user,
    ).select_related('agent').prefetch_related('messages')

    rooms_with_info = []
    for room in existing_rooms:
        unread = room.messages.filter(
            is_read=False,
        ).exclude(sender=request.user).count()
        last_msg = room.messages.order_by('-created_at').first()
        rooms_with_info.append({
            'room': room,
            'unread': unread,
            'last_message': last_msg,
        })

    return render(request, 'chat/client_list.html', {
        'agents': agents,
        'rooms': rooms_with_info,
        'agency': agency,
    })

@never_cache
@login_required
def client_chat(request, room_pk=None, agent_pk=None):
    """Страница чата клиента.
    Можно открыть существующую комнату по room_pk
    или создать новую с конкретным агентом по agent_pk
    или создать общий чат (agent=None).
    """
    agency = Agency.objects.first()

    if room_pk:
        # Открываем существующую комнату
        room = get_object_or_404(
            ChatRoom, pk=room_pk, client=request.user
        )
    else:
        # Создаём или открываем чат с выбранным агентом
        agent = None
        if agent_pk:
            agent = get_object_or_404(
                User, pk=agent_pk, agency=agency
            )
        room = get_or_create_room(request.user, agency, agent=agent)

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        reply_to_id = request.POST.get('reply_to')
        if text:
            reply_to = None
            if reply_to_id:
                reply_to = Message.objects.filter(pk=reply_to_id, room=room).first()
            Message.objects.create(
                room=room,
                sender=request.user,
                text=text,
                reply_to=reply_to,
            )
        
    room.messages.filter(
        is_read=False,
    ).exclude(sender=request.user).update(is_read=True)

    messages_qs = room.messages.select_related('sender').order_by('created_at')

    return render(request, 'chat/client_room.html', {
        'room': room,
        'chat_messages': messages_qs,
    })

@never_cache
@login_required
def client_chat_poll(request, room_pk):
    """HTMX polling для клиента."""
    room = get_object_or_404(ChatRoom, pk=room_pk, client=request.user)

    room.messages.filter(
        is_read=False,
    ).exclude(sender=request.user).update(is_read=True)

    messages_qs = room.messages.select_related('sender').order_by('created_at')

    return render(request, 'chat/_messages.html', {
        'room': room,
        'chat_messages': messages_qs
    })


@crm_required
def agent_chat_list(request):
    """Список чатов для сотрудника CRM."""
    from apps.accounts.models import UserProfile

    if request.user.is_agent:
        # Риелтор видит:
        # 1. Чаты где он назначен агентом
        # 2. Общие чаты (agent=None) — может подхватить
        personal_rooms = ChatRoom.objects.filter(
            agency=request.user.agency,
            agent=request.user,
        )
        general_rooms = ChatRoom.objects.filter(
            agency=request.user.agency,
            agent=None,
        )
        rooms = (personal_rooms | general_rooms).distinct()
    else:
        # Менеджер и admin видят все чаты агентства
        rooms = ChatRoom.objects.filter(
            agency=request.user.agency,
        )

    rooms = rooms.select_related(
        'client', 'agent'
    ).prefetch_related('messages').order_by('-created_at')

    rooms_with_unread = []
    for room in rooms:
        unread = room.messages.filter(
            is_read=False,
        ).exclude(sender=request.user).count()
        last_message = room.messages.order_by('-created_at').first()
        rooms_with_unread.append({
            'room': room,
            'unread': unread,
            'last_message': last_message,
            'is_general': room.agent is None,
        })

    # Сортируем — сначала непрочитанные
    rooms_with_unread.sort(key=lambda x: (
        -x['unread'],
        -(x['last_message'].created_at.timestamp()
          if x['last_message'] else 0)
    ))

    # Общее количество непрочитанных для бейджа
    total_unread = sum(r['unread'] for r in rooms_with_unread)

    return render(request, 'chat/agent_list.html', {
        'rooms': rooms_with_unread,
        'total_unread': total_unread,
    })

@never_cache
@crm_required
def agent_chat_room(request, pk):
    """Страница чата для риелтора в CRM."""
    room = get_object_or_404(
        ChatRoom, pk=pk, agency=request.user.agency
    )

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        reply_to_id = request.POST.get('reply_to')
        if text:
            reply_to = None
            if reply_to_id:
                reply_to = Message.objects.filter(pk=reply_to_id, room=room).first()
            Message.objects.create(
                room=room,
                sender=request.user,
                text=text,
                reply_to=reply_to,
            )
            if not room.agent:
                room.agent = request.user
                room.save()

    # Отмечаем сообщения клиента как прочитанные
    room.messages.filter(
        is_read=False,
    ).exclude(sender=request.user).update(is_read=True)

    messages_qs = room.messages.select_related('sender').order_by('created_at')

    return render(request, 'chat/agent_room.html', {
        'room': room,
        'chat_messages': messages_qs,
    })

@never_cache
@crm_required
def agent_chat_poll(request, pk):
    """HTMX polling для риелтора."""
    room = get_object_or_404(
        ChatRoom, pk=pk, agency=request.user.agency
    )

    room.messages.filter(
        is_read=False,
    ).exclude(sender=request.user).update(is_read=True)

    messages_qs = room.messages.select_related('sender').order_by('created_at')

    return render(request, 'chat/_messages.html', {
        'room': room,
        'chat_messages': messages_qs,
        'is_client': False,
    })
    
@crm_required
def agent_claim_room(request, pk):
    """Риелтор берёт общий чат себе."""
    if request.method == 'POST':
        room = get_object_or_404(
            ChatRoom, pk=pk,
            agency=request.user.agency,
            agent=None,
        )

        # Проверяем нет ли уже личного чата с этим клиентом
        existing_room = ChatRoom.objects.filter(
            agency=request.user.agency,
            client=room.client,
            agent=request.user,
        ).first()

        if existing_room:
            # Уже есть личный чат — редиректим туда
            messages.info(
                request,
                f'У вас уже есть личный чат с {room.client.get_full_name()}.'
            )
            return redirect('chat:agent_room', pk=existing_room.pk)

        # Назначаем себя агентом
        room.agent = request.user
        room.save(update_fields=['agent'])
        messages.success(
            request,
            f'Вы взяли чат с {room.client.get_full_name()} себе.'
        )

    return redirect('chat:agent_room', pk=pk)

@crm_required
def internal_chat_list(request):
    """Список внутренних чатов сотрудника."""
    chats = InternalChat.objects.filter(
        agency=request.user.agency,
        participants=request.user,
    ).prefetch_related('participants', 'messages').annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')

    chats_with_info = []
    for chat in chats:
        last_msg = chat.messages.order_by('-created_at').first()
        unread = chat.messages.exclude(
            sender=request.user
        ).exclude(
            read_by__user=request.user
        ).count()
        chats_with_info.append({
            'chat': chat,
            'display_name': chat.get_display_name(request.user),
            'last_message': last_msg,
            'unread': unread,
        })

    # Список коллег для создания нового чата
    colleagues = User.objects.filter(
        agency=request.user.agency,
        is_active=True,
    ).exclude(pk=request.user.pk)

    return render(request, 'chat/internal_list.html', {
        'chats': chats_with_info,
        'colleagues': colleagues,
    })


@crm_required
def internal_chat_start(request, user_pk):
    """Начать личный чат с коллегой (или открыть существующий)."""
    colleague = get_object_or_404(
        User, pk=user_pk, agency=request.user.agency
    )

    # Ищем существующий личный чат между этими двумя пользователями
    existing = InternalChat.objects.filter(
        agency=request.user.agency,
        is_group=False,
        participants=request.user,
    ).filter(participants=colleague).first()

    if existing:
        return redirect('chat:internal_room', pk=existing.pk)

    # Создаём новый личный чат
    chat = InternalChat.objects.create(
        agency=request.user.agency,
        is_group=False,
        created_by=request.user,
    )
    chat.participants.add(request.user, colleague)

    return redirect('chat:internal_room', pk=chat.pk)


@crm_required
def internal_chat_create_group(request):
    """Создание группового чата."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        participant_ids = request.POST.getlist('participants')

        if not name:
            messages.error(request, 'Укажите название группы.')
            return redirect('chat:internal_list')

        if len(participant_ids) < 2:
            messages.error(request, 'Выберите минимум 2 участника.')
            return redirect('chat:internal_list')

        chat = InternalChat.objects.create(
            agency=request.user.agency,
            name=name,
            is_group=True,
            created_by=request.user,
        )
        chat.participants.add(request.user)
        for pid in participant_ids:
            colleague = User.objects.filter(
                pk=pid, agency=request.user.agency
            ).first()
            if colleague:
                chat.participants.add(colleague)

        messages.success(request, f'Группа «{name}» создана.')
        return redirect('chat:internal_room', pk=chat.pk)

    return redirect('chat:internal_list')


@never_cache
@crm_required
def internal_chat_room(request, pk):
    """Страница внутреннего чата."""
    chat = get_object_or_404(
        InternalChat, pk=pk,
        agency=request.user.agency,
        participants=request.user,
    )

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        reply_to_id = request.POST.get('reply_to')
        if text:
            reply_to = None
            if reply_to_id:
                reply_to = InternalMessage.objects.filter(pk=reply_to_id, chat=chat).first()
            InternalMessage.objects.create(
                chat=chat,
                sender=request.user,
                text=text,
                reply_to=reply_to,
            )
        _mark_internal_read(chat, request.user)
        chat_messages = chat.messages.select_related('sender').order_by('created_at')
        return render(request, 'chat/_internal_messages.html', {
            'chat': chat,
            'chat_messages': chat_messages,
            'request': request,
        })

    _mark_internal_read(chat, request.user)
    chat_messages = chat.messages.select_related('sender').order_by('created_at')

    return render(request, 'chat/internal_room.html', {
        'chat': chat,
        'chat_messages': chat_messages,
        'display_name': chat.get_display_name(request.user),
    })


@never_cache
@crm_required
def internal_chat_poll(request, pk):
    """HTMX polling для внутреннего чата."""
    chat = get_object_or_404(
        InternalChat, pk=pk,
        agency=request.user.agency,
        participants=request.user,
    )
    _mark_internal_read(chat, request.user)
    chat_messages = chat.messages.select_related('sender').order_by('created_at')
    return render(request, 'chat/_internal_messages.html', {
        'chat': chat,
        'chat_messages': chat_messages,
        'request': request,
    })


def _mark_internal_read(chat, user):
    """Отмечает все сообщения чата как прочитанные текущим пользователем."""
    unread_messages = chat.messages.exclude(
        sender=user,
    ).exclude(
        read_by__user=user,
    )
    for msg in unread_messages:
        InternalMessageRead.objects.get_or_create(message=msg, user=user)