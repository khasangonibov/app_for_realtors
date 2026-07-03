from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from apps.accounts.decorators import crm_required
from .models import Task
from .forms import TaskForm


@crm_required
def task_list(request):
    # Базовый queryset — все задачи риелтора
    base_qs = Task.objects.filter(
        agency=request.user.agency,
        agent=request.user,
    ).select_related('contact', 'related_property')

    now = timezone.now()

    # Просроченные — не выполнены и срок прошёл
    overdue = base_qs.filter(is_done=False, due_date__lt=now)

    # Активные — не выполнены и срок ещё не прошёл
    active = base_qs.filter(is_done=False, due_date__gte=now)

    # Выполненные — последние 20
    done = base_qs.filter(is_done=True).order_by('-done_at')[:20]

    return render(request, 'tasks/list.html', {
        'overdue': overdue,
        'active': active,
        'done': done,
        'now': now,
    })

@crm_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, agency=request.user.agency)
        if form.is_valid():
            task = form.save(commit=False)
            task.agency = request.user.agency
            task.agent = request.user
            task.save()
            messages.success(request, 'Задача создана.')
            return redirect('tasks:list')
    else:
        form = TaskForm(agency=request.user.agency)

    return render(request, 'tasks/form.html', {
        'form': form,
        'title': 'Новая задача',
        'submit_label': 'Создать задачу',
    })


@crm_required
def task_edit(request, pk):
    task = get_object_or_404(
        Task, pk=pk, agency=request.user.agency
    )
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, agency=request.user.agency)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задача обновлена.')
            return redirect('tasks:list')
    else:
        form = TaskForm(instance=task, agency=request.user.agency)

    return render(request, 'tasks/form.html', {
        'form': form,
        'task': task,
        'title': 'Редактировать задачу',
        'submit_label': 'Сохранить',
    })


@crm_required
def task_done(request, pk):
    """Отметить задачу как выполненную — только POST."""
    if request.method == 'POST':
        task = get_object_or_404(
            Task, pk=pk, agency=request.user.agency
        )
        task.is_done = True
        task.done_at = timezone.now()
        task.save(update_fields=['is_done', 'done_at'])
        messages.success(request, f'Задача «{task.title}» выполнена.')
    return redirect('tasks:list')