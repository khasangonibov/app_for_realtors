from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum

from apps.accounts.decorators import crm_required
from .models import ManagementContract, Transaction, ManagementDocument, ActivityLog
from .forms import ManagementContractForm, TransactionForm, ManagementDocumentForm


def _log_action(contract, user, action):
    """Записывает действие в журнал договора."""
    ActivityLog.objects.create(contract=contract, user=user, action=action)


@crm_required
def contract_list(request):
    """Список договоров доверительного управления."""
    queryset = ManagementContract.objects.filter(
        agency=request.user.agency,
        is_deleted=False,
    ).select_related('related_property', 'owner', 'agent')

    if request.user.is_agent:
        queryset = queryset.filter(agent=request.user)

    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)

    paginator = Paginator(queryset, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'trust_management/list.html', {
        'contracts': page_obj,
        'page_obj': page_obj,
        'total_count': queryset.count(),
        'status_choices': ManagementContract.Status.choices,
        'current_status': status,
    })


@crm_required
def contract_create(request):
    if request.method == 'POST':
        form = ManagementContractForm(request.POST, agency=request.user.agency)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.agency = request.user.agency
            contract.save()
            _log_action(contract, request.user, 'Договор создан')
            messages.success(request, 'Договор управления создан.')
            return redirect('trust_management:detail', pk=contract.pk)
    else:
        form = ManagementContractForm(agency=request.user.agency)

    return render(request, 'trust_management/form.html', {
        'form': form,
        'title': 'Новый договор управления',
        'submit_label': 'Создать договор',
    })


@crm_required
def contract_edit(request, pk):
    queryset = ManagementContract.objects.filter(agency=request.user.agency, is_deleted=False,)

    if request.user.is_agent:
        queryset = queryset.filter(agent=request.user)

    contract = get_object_or_404(queryset, pk=pk)
    
    if request.method == 'POST':
        form = ManagementContractForm(
            request.POST, instance=contract, agency=request.user.agency
        )
        if form.is_valid():
            form.save()
            _log_action(contract, request.user, 'Договор отредактирован')
            messages.success(request, 'Договор обновлён.')
            return redirect('trust_management:detail', pk=contract.pk)
    else:
        form = ManagementContractForm(instance=contract, agency=request.user.agency)

    return render(request, 'trust_management/form.html', {
        'form': form,
        'contract': contract,
        'title': 'Редактировать договор',
        'submit_label': 'Сохранить',
    })


@crm_required
def contract_detail(request, pk):
    """Карточка договора — финансы, документы, журнал."""
    queryset = ManagementContract.objects.filter(agency=request.user.agency, is_deleted=False,)

    # Обычный риелтор видит только свои договоры управления
    if request.user.is_agent:
        queryset = queryset.filter(agent=request.user)

    contract = get_object_or_404(queryset, pk=pk)

    transactions = contract.transactions.all()
    documents = contract.documents.select_related('uploaded_by')
    activity_log = contract.activity_log.select_related('user')[:20]

    # Форма добавления транзакции
    if request.method == 'POST' and 'add_transaction' in request.POST:
        t_form = TransactionForm(request.POST)
        if t_form.is_valid():
            transaction = t_form.save(commit=False)
            transaction.contract = contract
            transaction.created_by = request.user
            transaction.save()
            _log_action(
                contract, request.user,
                f'Добавлена {transaction.get_type_display().lower()}: {transaction.amount} ₽'
            )
            messages.success(request, 'Запись добавлена.')
            return redirect('trust_management:detail', pk=pk)
    else:
        t_form = TransactionForm()

    # Форма загрузки документа
    if request.method == 'POST' and 'add_document' in request.POST:
        d_form = ManagementDocumentForm(request.POST, request.FILES)
        if d_form.is_valid():
            document = d_form.save(commit=False)
            document.contract = contract
            document.uploaded_by = request.user
            document.save()
            _log_action(contract, request.user, f'Загружен документ: {document.name}')
            messages.success(request, 'Документ загружен.')
            return redirect('trust_management:detail', pk=pk)
    else:
        d_form = ManagementDocumentForm()

    # Разбивка доходов/расходов по категориям
    income_by_category = transactions.filter(
        type=Transaction.Type.INCOME
    ).values('category').annotate(total=Sum('amount'))
    expense_by_category = transactions.filter(
        type=Transaction.Type.EXPENSE
    ).values('category').annotate(total=Sum('amount'))

    return render(request, 'trust_management/detail.html', {
        'contract': contract,
        'transactions': transactions,
        'documents': documents,
        'activity_log': activity_log,
        't_form': t_form,
        'd_form': d_form,
        'income_by_category': income_by_category,
        'expense_by_category': expense_by_category,
    })


@crm_required
def transaction_delete(request, pk, transaction_pk):
    queryset = ManagementContract.objects.filter(agency=request.user.agency, is_deleted=False,)
    if request.user.is_agent:
        queryset = queryset.filter(agent=request.user)
    
    contract = get_object_or_404(queryset, pk=pk)
    
    transaction = get_object_or_404(
        Transaction, pk=transaction_pk, contract=contract
    )
    if request.method == 'POST':
        _log_action(
            contract, request.user,
            f'Удалена запись: {transaction.amount} ₽ ({transaction.get_category_display()})'
        )
        transaction.delete()
        messages.success(request, 'Запись удалена.')
    return redirect('trust_management:detail', pk=pk)


@crm_required
def document_delete(request, pk, document_pk):
    queryset = ManagementContract.objects.filter(agency=request.user.agency, is_deleted=False,)
    if request.user.is_agent:
        queryset = queryset.filter(agent=request.user)
        
    contract = get_object_or_404(queryset, pk=pk)
    
    document = get_object_or_404(
        ManagementDocument, pk=document_pk, contract=contract
    )
    if request.method == 'POST':
        _log_action(contract, request.user, f'Удалён документ: {document.name}')
        document.file.delete(save=False)
        document.delete()
        messages.success(request, 'Документ удалён.')
    return redirect('trust_management:detail', pk=pk)


@crm_required
def contract_report(request, pk):
    """Отчёт для клиента — доходы/расходы за период."""
    queryset = ManagementContract.objects.filter(agency=request.user.agency, is_deleted=False,)

    if request.user.is_agent:
        queryset = queryset.filter(agent=request.user)

    contract = get_object_or_404(queryset, pk=pk)

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    transactions = contract.transactions.all()
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)

    total_income = transactions.filter(
        type=Transaction.Type.INCOME
    ).aggregate(total=Sum('amount'))['total'] or 0
    total_expense = transactions.filter(
        type=Transaction.Type.EXPENSE
    ).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'trust_management/report.html', {
        'contract': contract,
        'transactions': transactions.order_by('date'),
        'total_income': total_income,
        'total_expense': total_expense,
        'net_income': total_income - total_expense,
        'date_from': date_from,
        'date_to': date_to,
    })