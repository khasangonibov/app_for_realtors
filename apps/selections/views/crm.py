from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from apps.accounts.decorators import crm_required
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
    """Страница подборки в CRM.
    Просматривать может любой сотрудник, добавлять/удалять объекты —
    только создатель подборки или менеджер/админ.
    """
    selection = get_object_or_404(
        Selection, pk=pk, agency=request.user.agency
    )

    can_edit = (
        not request.user.is_agent
        or selection.agent == request.user
    )

    items = selection.items.select_related('property')

    if request.method == 'POST':
        if not can_edit:
            messages.error(request, 'Редактировать подборку может только её создатель.')
            return redirect('selections:detail', pk=pk)

        item_form = SelectionItemForm(
            request.POST,
            agency=request.user.agency,
            selection=selection,
        )
        if item_form.is_valid():
            item = item_form.save(commit=False)
            item.selection = selection
            item.save()
            messages.success(request, 'Объект добавлен в подборку.')
            return redirect('selections:detail', pk=pk)
    else:
        item_form = SelectionItemForm(
            agency=request.user.agency,
            selection=selection,
        )

    return render(request, 'selections/crm/detail.html', {
        'selection': selection,
        'items': items,
        'item_form': item_form,
        'can_edit': can_edit,
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