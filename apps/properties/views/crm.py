"""
CRM-views для работы с объектами недвижимости.
Все views требуют авторизации — декоратор @login_required.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q as models_Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.properties.models import Property, PropertyPhoto
from apps.properties.forms import PropertyFilterForm, PropertyForm
from apps.accounts.decorators import crm_required

@crm_required
def property_list(request):
    """Список объектов для риелтора.

    Риелтор видит только объекты своего агентства.
    Администратор/менеджер видит все объекты агентства.
    Фильтрация через GET-параметры (?status=active&city=Москва).
    """
    # Базовый queryset — только объекты агентства текущего пользователя.
    # Это главное правило мультитенантности: никто не видит чужие данные.
    queryset = Property.objects.filter(
        agency=request.user.agency
    ).select_related(
        'agent',   # загружаем агента одним JOIN, а не N отдельных запросов
    ).prefetch_related(
        'photos',  # фото тоже сразу, чтобы показать обложку в карточке
    )

    # Риелтор видит только свои объекты,
    # менеджер и admin — все объекты агентства
    if request.user.is_agent:
        queryset = queryset.filter(agent=request.user)

    # Применяем фильтры из GET-параметров
    form = PropertyFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('status'):
            queryset = queryset.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('deal_type'):
            queryset = queryset.filter(deal_type=form.cleaned_data['deal_type'])
        if form.cleaned_data.get('property_type'):
            queryset = queryset.filter(property_type=form.cleaned_data['property_type'])
        if form.cleaned_data.get('city'):
            queryset = queryset.filter(city__icontains=form.cleaned_data['city'])
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            queryset = queryset.filter(
                # ищем по нескольким полям сразу через OR
                models_Q(title__icontains=search) |
                models_Q(street__icontains=search) |
                models_Q(description__icontains=search)
            )

    return render(request, 'properties/crm/list.html', {
        'properties': queryset,
        'form': form,
        'total_count': queryset.count(),
    })
    
@crm_required
def property_create(request):
    """Создание нового объекта недвижимости.
    agency и agent проставляются автоматически из текущего пользователя —
    риелтор не может создать объект в чужом агентстве.
    """
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            # Привязываем к агентству и агенту текущего пользователя
            property_obj.agency = request.user.agency
            property_obj.agent = request.user
            property_obj.save()
            messages.success(request, 'Объект успешно создан.')
            return redirect('properties:list')
    else:
        form = PropertyForm()

    return render(request, 'properties/crm/form.html', {
        'form': form,
        'title': 'Новый объект',
        'submit_label': 'Создать объект',
    })


@crm_required
def property_edit(request, pk):
    """Редактирование существующего объекта.
    Проверяем что объект принадлежит агентству текущего пользователя —
    риелтор не может редактировать чужие объекты.
    """
    property_obj = get_object_or_404(
        Property,
        pk=pk,
        agency=request.user.agency,
    )

    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Объект успешно обновлён.')
            return redirect('properties:list')
    else:
        form = PropertyForm(instance=property_obj)

    return render(request, 'properties/crm/form.html', {
        'form': form,
        'property': property_obj,
        'title': 'Редактировать объект',
        'submit_label': 'Сохранить изменения',
    })
    
@crm_required
@require_POST
def photo_upload(request, pk):
    """Загрузка фото объекта — принимает файлы через AJAX/форму.
    Возвращает JSON с данными загруженного фото.
    """
    property_obj = get_object_or_404(
        Property, pk=pk, agency=request.user.agency
    )

    files = request.FILES.getlist('photos')
    if not files:
        return JsonResponse({'error': 'Файлы не выбраны'}, status=400)

    uploaded = []
    for file in files:
        photo = PropertyPhoto.objects.create(
            property=property_obj,
            image=file,
            # Если фото первое — автоматически делаем обложкой
            is_cover=not property_obj.photos.exists(),
        )
        uploaded.append({
            'id': str(photo.pk),
            'url': photo.image.url,
            'is_cover': photo.is_cover,
        })

    return JsonResponse({'photos': uploaded})


@crm_required
@require_POST
def photo_delete(request, pk, photo_pk):
    """Удаление фото объекта."""
    property_obj = get_object_or_404(
        Property, pk=pk, agency=request.user.agency
    )
    photo = get_object_or_404(
        PropertyPhoto, pk=photo_pk, property=property_obj
    )
    photo.image.delete(save=False)  # удаляем файл с диска
    photo.delete()
    return JsonResponse({'status': 'ok'})


@crm_required
@require_POST
def photo_set_cover(request, pk, photo_pk):
    """Установить фото как обложку."""
    property_obj = get_object_or_404(
        Property, pk=pk, agency=request.user.agency
    )
    photo = get_object_or_404(
        PropertyPhoto, pk=photo_pk, property=property_obj
    )
    # Снимаем флаг со всех остальных фото
    PropertyPhoto.objects.filter(
        property=property_obj, is_cover=True
    ).update(is_cover=False)
    photo.is_cover = True
    photo.save(update_fields=['is_cover'])
    return JsonResponse({'status': 'ok'})