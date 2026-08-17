from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q

from apps.accounts.decorators import crm_required
from apps.core.exports import create_excel_response, style_header_row, finalize_excel
from .models import Deal
from .forms import DealForm, DealFilterForm


def _base_queryset(user):
    """Базовая выборка сделок агентства — видно всем сотрудникам."""
    return Deal.objects.filter(agency=user.agency, is_deleted=False)


def _apply_filters(form, queryset):
    """Фильтрация queryset по данным DealFilterForm."""
    if not form.is_valid():
        return queryset

    if form.cleaned_data.get('stage'):
        queryset = queryset.filter(stage=form.cleaned_data['stage'])
    if form.cleaned_data.get('agent'):
        queryset = queryset.filter(agent=form.cleaned_data['agent'])
    if form.cleaned_data.get('search'):
        search = form.cleaned_data['search']
        queryset = queryset.filter(
            Q(property__city__icontains=search) |
            Q(property__street__icontains=search) |
            Q(buyer_contact__first_name__icontains=search) |
            Q(buyer_contact__last_name__icontains=search) |
            Q(seller_contact__first_name__icontains=search) |
            Q(seller_contact__last_name__icontains=search)
        )
    return queryset


@crm_required
def deal_board(request):
    """Kanban-доска сделок — видно всем сотрудникам агентства,
    с фильтрами по стадии, риелтору и поиском.
    """
    queryset = _base_queryset(request.user).select_related(
        'property', 'buyer_contact', 'seller_contact', 'agent'
    )

    form = DealFilterForm(request.GET, agency=request.user.agency)
    queryset = _apply_filters(form, queryset)

    active_stages = [
        Deal.Stage.NEGOTIATION,
        Deal.Stage.DEPOSIT,
        Deal.Stage.DOCUMENTS,
        Deal.Stage.REGISTRATION,
    ]

    board = {}
    for stage in active_stages:
        board[stage] = {
            'label': Deal.Stage(stage).label,
            'deals': queryset.filter(stage=stage),
        }

    finished = queryset.filter(
        stage__in=[Deal.Stage.CLOSED, Deal.Stage.CANCELLED]
    ).order_by('-close_date')[:10]

    return render(request, 'deals/board.html', {
        'board': board,
        'finished': finished,
        'total_count': queryset.count(),
        'form': form,
    })


@crm_required
def deal_create(request):
    if request.method == 'POST':
        form = DealForm(request.POST, agency=request.user.agency)
        if form.is_valid():
            deal = form.save(commit=False)
            deal.agency = request.user.agency
            deal.agent = request.user
            deal.save()
            messages.success(request, 'Сделка создана.')
            return redirect('deals:board')
    else:
        form = DealForm(agency=request.user.agency)

    return render(request, 'deals/form.html', {
        'form': form,
        'title': 'Новая сделка',
        'submit_label': 'Создать сделку',
    })


@crm_required
def deal_edit(request, pk):
    deal = get_object_or_404(
        Deal, pk=pk, agency=request.user.agency
    )

    if request.user.is_agent and deal.agent != request.user:
        messages.error(request, 'Редактировать сделку может только назначенный риелтор.')
        return redirect('deals:board')

    if request.method == 'POST':
        form = DealForm(request.POST, instance=deal, agency=request.user.agency)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сделка обновлена.')
            return redirect('deals:board')
    else:
        form = DealForm(instance=deal, agency=request.user.agency)

    return render(request, 'deals/form.html', {
        'form': form,
        'deal': deal,
        'title': 'Редактировать сделку',
        'submit_label': 'Сохранить',
    })


@crm_required
def deal_export_excel(request):
    """Экспорт сделок в Excel — только те, что проходят по текущим фильтрам."""
    queryset = _base_queryset(request.user).select_related(
        'property', 'buyer_contact', 'seller_contact', 'agent'
    )

    form = DealFilterForm(request.GET, agency=request.user.agency)
    queryset = _apply_filters(form, queryset)

    from datetime import datetime
    filename = f"deals_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    wb, ws, response = create_excel_response(filename)

    ws.title = 'Сделки'

    headers = [
        '№', 'Стадия', 'Объект', 'Город',
        'Покупатель', 'Телефон покупателя',
        'Продавец', 'Риелтор',
        'Согласованная цена, ₽', 'Комиссия, ₽',
        'Задаток, ₽', 'Дата задатка',
        'Дата договора', 'Дата закрытия',
        'Дата создания',
    ]
    style_header_row(ws, headers)

    for i, deal in enumerate(queryset, 1):
        ws.append([
            i,
            deal.get_stage_display(),
            str(deal.property) if deal.property else '',
            deal.property.city if deal.property else '',
            deal.buyer_contact.full_name if deal.buyer_contact else '',
            deal.buyer_contact.phone if deal.buyer_contact else '',
            deal.seller_contact.full_name if deal.seller_contact else '',
            deal.agent.get_full_name() if deal.agent else '',
            float(deal.price_agreed) if deal.price_agreed else '',
            float(deal.commission_total) if deal.commission_total else '',
            float(deal.deposit_amount) if deal.deposit_amount else '',
            deal.deposit_date.strftime('%d.%m.%Y') if deal.deposit_date else '',
            deal.contract_date.strftime('%d.%m.%Y') if deal.contract_date else '',
            deal.close_date.strftime('%d.%m.%Y') if deal.close_date else '',
            deal.created_at.strftime('%d.%m.%Y') if deal.created_at else '',
        ])

    return finalize_excel(wb, ws, response, start_row=2, col_count=len(headers))


@crm_required
def deal_delete(request, pk):
    """Мягкое удаление сделки — только назначенный агент, менеджер, админ.
    """
    deal_obj = get_object_or_404(
        Deal, pk=pk, agency=request.user.agency, is_deleted=False,
    )

    if request.user.is_agent and deal_obj.agent != request.user:
        messages.error(request, 'Удалить сделку может только назначенный риелтор.')
        return redirect('deals:board')

    if request.method == 'POST':
        deal_obj.soft_delete()
        messages.success(request, f'Сделка «{deal_obj}» удалёна.')
        return redirect('deals:board')

    return render(request, 'deals/delete_confirm.html', {
        'deal': deal_obj,
    })