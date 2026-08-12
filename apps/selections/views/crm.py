from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from apps.accounts.decorators import crm_required
from apps.properties.models import Property
from apps.selections.models import Selection, SelectionItem
from apps.selections.forms import SelectionForm, SelectionItemForm


@crm_required
def selection_list(request):
    """Список подборок риелтора."""
    queryset = Selection.objects.filter(
        agency=request.user.agency
    ).select_related('contact', 'agent').prefetch_related('items')

    return render(request, 'selections/crm/list.html', {
        'selections': queryset,
        'total_count': queryset.count(),
    })


@crm_required
def selection_create(request):
    """Создание новой подборки."""
    if request.method == 'POST':
        form = SelectionForm(request.POST, agency=request.user.agency)
        if form.is_valid():
            selection = form.save(commit=False)
            selection.agency = request.user.agency
            selection.agent = request.user
            selection.save()
            messages.success(request, 'Подборка создана. Добавьте объекты.')
            return redirect('selections:detail', pk=selection.pk)
    else:
        form = SelectionForm(agency=request.user.agency)

    return render(request, 'selections/crm/form.html', {
        'form': form,
        'title': 'Новая подборка',
        'submit_label': 'Создать подборку',
    })


@crm_required
def selection_detail(request, pk):
    """Страница подборки — список добавленных + панель выбора объектов
    с фильтрами и карточками для быстрого добавления.
    """
    selection = get_object_or_404(
        Selection, pk=pk, agency=request.user.agency
    )

    can_edit = (
        not request.user.is_agent
        or selection.agent == request.user
    )

    items = selection.items.select_related('property').prefetch_related('property__photos')
    added_property_ids = list(items.values_list('property_id', flat=True))

    # ── Обработка добавления объектов (множественный выбор) ────────────────
    if request.method == 'POST':
        if not can_edit:
            messages.error(request, 'Редактировать подборку может только её создатель.')
            return redirect('selections:detail', pk=pk)

        selected_ids = request.POST.getlist('property_ids')
        added_count = 0
        for prop_id in selected_ids:
            prop = Property.objects.filter(
                pk=prop_id, agency=request.user.agency, is_published=True,
            ).first()
            if prop and not SelectionItem.objects.filter(
                selection=selection, property=prop
            ).exists():
                SelectionItem.objects.create(selection=selection, property=prop)
                added_count += 1

        if added_count:
            messages.success(request, f'Добавлено объектов: {added_count}.')
        return redirect('selections:detail', pk=pk)

    # ── Фильтры для панели выбора объектов ──────────────────────────────────
    available_properties = Property.objects.filter(
        agency=request.user.agency,
        is_published=True,
    ).exclude(pk__in=added_property_ids).select_related('agent').prefetch_related('photos')

    deal_type = request.GET.get('deal_type', '')
    property_type = request.GET.get('property_type', '')
    city = request.GET.get('city', '')
    rooms = request.GET.get('rooms', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    search = request.GET.get('search', '').strip()

    if deal_type:
        available_properties = available_properties.filter(deal_type=deal_type)
    if property_type:
        available_properties = available_properties.filter(property_type=property_type)
    if city:
        available_properties = available_properties.filter(city__icontains=city)
    if rooms:
        available_properties = available_properties.filter(rooms_count=rooms)
    if price_min:
        available_properties = available_properties.filter(price__gte=price_min)
    if price_max:
        available_properties = available_properties.filter(price__lte=price_max)
    if search:
        available_properties = available_properties.filter(
            Q(city__icontains=search) |
            Q(street__icontains=search) |
            Q(title__icontains=search)
        )

    available_properties = available_properties.order_by('-created_at')

    # Список городов для фильтра
    cities = Property.objects.filter(
        agency=request.user.agency, is_published=True,
    ).exclude(pk__in=added_property_ids).values_list(
        'city', flat=True
    ).distinct().order_by('city')

    # Пагинация панели выбора
    paginator = Paginator(available_properties, 9)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'selections/crm/detail.html', {
        'selection': selection,
        'items': items,
        'can_edit': can_edit,
        'available_properties': page_obj,
        'page_obj': page_obj,
        'cities': cities,
        'deal_types': Property.DealType.choices,
        'property_types': Property.PropertyType.choices,
        'current_deal_type': deal_type,
        'current_property_type': property_type,
        'current_city': city,
        'current_rooms': rooms,
        'current_price_min': price_min,
        'current_price_max': price_max,
        'current_search': search,
    })

@crm_required
def selection_item_delete(request, pk, item_pk):
    selection = get_object_or_404(
        Selection, pk=pk, agency=request.user.agency
    )

    can_edit = (
        not request.user.is_agent
        or selection.agent == request.user
    )
    if not can_edit:
        messages.error(request, 'Удалять объекты может только создатель подборки.')
        return redirect('selections:detail', pk=pk)

    item = get_object_or_404(SelectionItem, pk=item_pk, selection=selection)

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Объект удалён из подборки.')

    return redirect('selections:detail', pk=pk)