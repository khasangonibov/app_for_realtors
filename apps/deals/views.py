from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from apps.accounts.decorators import crm_required
from .models import Deal
from .forms import DealForm


@crm_required
def deal_board(request):
    """Kanban-доска сделок по стадиям."""
    queryset = Deal.objects.filter(
        agency=request.user.agency
    ).select_related('property', 'buyer_contact', 'agent')

    if request.user.is_agent:
        queryset = queryset.filter(agent=request.user)

    # Группируем сделки по стадиям для kanban
    # Исключаем закрытые и отменённые — они в отдельном списке
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

    # Закрытые и отменённые сделки — отдельным списком внизу
    finished = queryset.filter(
        stage__in=[Deal.Stage.CLOSED, Deal.Stage.CANCELLED]
    ).order_by('-close_date')[:10]

    return render(request, 'deals/board.html', {
        'board': board,
        'finished': finished,
        'total_count': queryset.count(),
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
        'title': f'Редактировать сделку',
        'submit_label': 'Сохранить',
    })