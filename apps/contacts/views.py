from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q

from .models import Contact, ContactActivity
from .forms import ContactForm, ActivityForm


@login_required
def contact_list(request):
    """Список контактов агентства с поиском и фильтрами."""
    queryset = Contact.objects.filter(
        agency=request.user.agency
    ).select_related('agent')

    # Риелтор видит только своих контактов
    if request.user.is_agent:
        queryset = queryset.filter(agent=request.user)

    # Поиск
    search = request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )

    # Фильтр по статусу
    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)

    # Фильтр по типу
    contact_type = request.GET.get('contact_type', '')
    if contact_type:
        queryset = queryset.filter(contact_type=contact_type)

    return render(request, 'contacts/list.html', {
        'contacts': queryset,
        'total_count': queryset.count(),
        'status_choices': Contact.Status.choices,
        'type_choices': Contact.ContactType.choices,
        'current_status': status,
        'current_type': contact_type,
        'search': search,
    })


@login_required
def contact_detail(request, pk):
    """Карточка контакта — данные + история активностей."""
    contact = get_object_or_404(
        Contact, pk=pk, agency=request.user.agency
    )
    activities = contact.activities.select_related('agent')

    # Форма добавления активности
    if request.method == 'POST':
        activity_form = ActivityForm(request.POST)
        if activity_form.is_valid():
            activity = activity_form.save(commit=False)
            activity.contact = contact
            activity.agent = request.user
            activity.save()
            messages.success(request, 'Активность добавлена.')
            return redirect('contacts:detail', pk=pk)
    else:
        activity_form = ActivityForm()

    return render(request, 'contacts/detail.html', {
        'contact': contact,
        'activities': activities,
        'activity_form': activity_form,
    })


@login_required
def contact_create(request):
    """Создание нового контакта."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.agency = request.user.agency
            contact.agent = request.user
            contact.save()
            messages.success(request, 'Контакт успешно создан.')
            return redirect('contacts:detail', pk=contact.pk)
    else:
        form = ContactForm()

    return render(request, 'contacts/form.html', {
        'form': form,
        'title': 'Новый контакт',
        'submit_label': 'Создать контакт',
    })


@login_required
def contact_edit(request, pk):
    """Редактирование контакта."""
    contact = get_object_or_404(
        Contact, pk=pk, agency=request.user.agency
    )

    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, 'Контакт обновлён.')
            return redirect('contacts:detail', pk=contact.pk)
    else:
        form = ContactForm(instance=contact)

    return render(request, 'contacts/form.html', {
        'form': form,
        'contact': contact,
        'title': f'Редактировать: {contact.full_name}',
        'submit_label': 'Сохранить',
    })