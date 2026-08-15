from django.db import models
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from apps.accounts.decorators import crm_required
from .models import Task
from .forms import TaskCompletionForm, TaskForm


@crm_required
def task_list(request):
    queryset = Task.objects.filter(
        agency=request.user.agency,
    ).select_related('contact', 'related_property', 'agent', 'assigned_by')

    if request.user.is_agent:
        queryset = queryset.filter(agent=request.user)

    now = timezone.now()

    # Отклонённые — отдельная графа, показываем и риелтору, и постановщику
    rejected = queryset.filter(is_done=False, was_rejected=True)

    # Просроченные и активные — исключаем отклонённые, у них своя графа
    overdue = queryset.filter(is_done=False, was_rejected=False, due_date__lt=now)
    active = queryset.filter(is_done=False, was_rejected=False, due_date__gte=now)

    pending_approval = Task.objects.filter(
        agency=request.user.agency,
        is_done=True,
        is_approved=False,
    ).exclude(assigned_by=None).exclude(assigned_by=models.F('agent'))

    if request.user.is_agent:
        pending_approval = pending_approval.none()
    else:
        pending_approval = pending_approval.select_related('agent', 'contact')

    done = queryset.filter(is_done=True).select_related('contact')
    done = [t for t in done if t.is_fully_completed][:20]

    return render(request, 'tasks/list.html', {
        'overdue': overdue,
        'active': active,
        'rejected': rejected,
        'pending_approval': pending_approval,
        'done': done,
        'now': now,
    })

@crm_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(
            request.POST, agency=request.user.agency, current_user=request.user,
        )
        if form.is_valid():
            task = form.save(commit=False)
            task.agency = request.user.agency
            task.assigned_by = request.user

            if 'agent' in form.cleaned_data:
                task.agent = form.cleaned_data['agent']
            else:
                task.agent = request.user

            task.save()
            messages.success(request, 'Задача создана.')
            return redirect('tasks:list')
    else:
        form = TaskForm(agency=request.user.agency, current_user=request.user)

    return render(request, 'tasks/form.html', {
        'form': form,
        'title': 'Новая задача',
        'submit_label': 'Создать задачу',
    })


@crm_required
def task_edit(request, pk):
    """Редактировать может исполнитель, менеджер или админ.
    Но если задачу назначил кто-то другой (не сам себе) —
    риелтор может только смотреть детали, не редактировать поля.
    """
    queryset = Task.objects.filter(agency=request.user.agency)
    if request.user.is_agent:
        queryset = queryset.filter(agent=request.user)
    task = get_object_or_404(queryset, pk=pk)

    # Риелтору, которому назначили задачу руководитель, редактирование закрыто —
    # только просмотр и кнопка "Выполнено"
    is_readonly_for_agent = (
        request.user.is_agent
        and task.needs_approval
    )

    if is_readonly_for_agent:
        return render(request, 'tasks/detail_readonly.html', {
            'task': task,
        })

    if request.method == 'POST':
        form = TaskForm(
            request.POST, instance=task,
            agency=request.user.agency, current_user=request.user,
        )
        if form.is_valid():
            task = form.save(commit=False)
            if 'agent' in form.cleaned_data:
                task.agent = form.cleaned_data['agent']
            task.save()
            messages.success(request, 'Задача обновлена.')
            return redirect('tasks:list')
    else:
        form = TaskForm(
            instance=task,
            agency=request.user.agency, current_user=request.user,
        )

    return render(request, 'tasks/form.html', {
        'form': form,
        'task': task,
        'title': 'Редактировать задачу',
        'submit_label': 'Сохранить',
    })


@crm_required
def task_done(request, pk):
    """Исполнитель отмечает задачу как сделанную с комментарием.
    Если задачу назначил кто-то другой — уходит на подтверждение.
    """
    queryset = Task.objects.filter(agency=request.user.agency)
    if request.user.is_agent:
        queryset = queryset.filter(agent=request.user)
    task = get_object_or_404(queryset, pk=pk)

    if request.method == 'POST':
        form = TaskCompletionForm(request.POST)
        if form.is_valid():
            task.is_done = True
            task.done_at = timezone.now()
            task.completion_comment = form.cleaned_data['comment']
            # Если задачу выполняют повторно после отклонения — сбрасываем флаг
            task.was_rejected = False
            task.save(update_fields=['is_done', 'done_at', 'completion_comment', 'was_rejected'])

            if task.needs_approval:
                messages.success(
                    request,
                    f'Задача «{task.title}» отмечена выполненной. '
                    f'Ожидает подтверждения от {task.assigned_by.get_full_name()}.'
                )
            else:
                messages.success(request, f'Задача «{task.title}» выполнена.')
            return redirect('tasks:list')
        else:
            messages.error(request, 'Укажите комментарий к выполнению.')
            return redirect('tasks:edit', pk=pk)

    # GET — показываем форму комментария перед подтверждением
    form = TaskCompletionForm()
    return render(request, 'tasks/complete_form.html', {
        'task': task,
        'form': form,
    })


@crm_required
def task_approve(request, pk):
    task = get_object_or_404(Task, pk=pk, agency=request.user.agency)

    if request.user.is_agent and task.assigned_by != request.user:
        messages.error(request, 'Подтвердить задачу может только тот, кто её назначил.')
        return redirect('tasks:list')

    if request.method == 'POST':
        task.is_approved = True
        task.approved_at = timezone.now()
        task.approved_by = request.user
        task.was_rejected = False
        task.save(update_fields=['is_approved', 'approved_at', 'approved_by', 'was_rejected'])
        messages.success(request, f'Выполнение задачи «{task.title}» подтверждено.')

    return redirect('tasks:list')


@crm_required
def task_reject(request, pk):
    """Отклонение выполнения — возвращает задачу в активные,
    с указанием причины и пометкой was_rejected для фронтенда.
    """
    task = get_object_or_404(Task, pk=pk, agency=request.user.agency)

    if request.user.is_agent and task.assigned_by != request.user:
        messages.error(request, 'Отклонить может только тот, кто назначил задачу.')
        return redirect('tasks:list')

    if request.method == 'POST':
        rejection_comment = request.POST.get('rejection_comment', '').strip()
        task.is_done = False
        task.done_at = None
        task.was_rejected = True
        task.rejection_comment = rejection_comment
        task.save(update_fields=['is_done', 'done_at', 'was_rejected', 'rejection_comment'])
        messages.warning(request, f'Выполнение задачи «{task.title}» отклонено, задача возвращена в работу.')

    return redirect('tasks:list')