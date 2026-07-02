from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404

from apps.selections.models import Selection, SelectionItem


def selection_detail(request, token):
    """Публичная страница подборки — доступна без авторизации по токену.
    Клиент может просматривать объекты и оставлять реакции.
    """
    selection = get_object_or_404(Selection, public_token=token)
    items = selection.items.select_related(
        'property', 'property__agency'
    ).prefetch_related('property__photos')

    return render(request, 'selections/public_detail.html', {
        'selection': selection,
        'items': items,
    })


def selection_item_react(request, token, item_pk):
    """Клиент ставит реакцию на объект в подборке.
    Принимает только POST-запросы.
    """
    if request.method != 'POST':
        raise Http404

    selection = get_object_or_404(Selection, public_token=token)
    item = get_object_or_404(SelectionItem, pk=item_pk, selection=selection)

    status = request.POST.get('status')
    if status in SelectionItem.ClientStatus.values:
        item.client_status = status
        item.save(update_fields=['client_status'])

    return redirect('selection_public:detail', token=token)