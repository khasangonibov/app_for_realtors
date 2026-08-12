"""
CRM-views для работы с объектами недвижимости.
Все views требуют авторизации — декоратор @crm_required.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q 
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from apps.properties.models import Property, PropertyPhoto, PropertyFeature
from apps.properties.forms import PropertyFilterForm, PropertyForm, PropertyFeatureFormSet, FEATURE_TEMPLATES
from apps.accounts.decorators import crm_required
from apps.core.exports import (
    create_excel_response, style_header_row, finalize_excel
)

# Объектов на страницу списка — кратно 3 колонкам сетки
PROPERTIES_PER_PAGE = 12

def _base_queryset(user):
    """Базовая выборка объектов агентства — одна точка правды.
    Используется списком, расчётом страницы при возврате из формы
    и экспортом: если правило видимости разойдётся между ними,
    номера страниц при редиректе перестанут совпадать со списком.
    """
    return Property.objects.filter(agency=user.agency)


def _apply_filters(form, queryset):
    """Фильтрация queryset по данным PropertyFilterForm.
    Вынесена отдельно, чтобы список и расчёт страницы при
    возврате из формы редактирования работали одинаково.
    """
    if not form.is_valid():
        return queryset

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
            Q(title__icontains=search) |
            Q(street__icontains=search) |
            Q(description__icontains=search)
        )
    return queryset


def _redirect_to_list_at(request, property_obj):
    """Возврат в список на то место, где стоит объект:
    те же фильтры, правильная страница, якорь на карточку.

    Страницу пересчитываем, а не берём из 'back' — после правки
    объект мог сместиться (например, сменился статус и он выпал
    из активного фильтра).
    """
    from urllib.parse import parse_qs, urlencode
    from django.urls import reverse

    back = request.POST.get('back') or request.GET.get('back') or ''
    params = {k: v[0] for k, v in parse_qs(back).items() if k != 'page'}

    queryset = _apply_filters(
        PropertyFilterForm(params), _base_queryset(request.user)
    )

    pks = list(queryset.values_list('pk', flat=True))
    url = reverse('properties:list')

    if property_obj.pk not in pks:
        # Объект больше не проходит по фильтрам — показываем список без них
        messages.info(
            request,
            'Объект сохранён, но не попадает под текущие фильтры списка.'
        )
        return redirect(url)

    page = pks.index(property_obj.pk) // PROPERTIES_PER_PAGE + 1
    if page > 1:
        params['page'] = page

    query = urlencode(params)
    return redirect(f'{url}?{query}#property-{property_obj.pk}' if query
                    else f'{url}#property-{property_obj.pk}')



@crm_required
def property_list(request):
    queryset = _base_queryset(request.user).select_related(
        'agent'
    ).prefetch_related('photos')

    form = PropertyFilterForm(request.GET)
    queryset = _apply_filters(form, queryset)
    
    total_count = queryset.count()

    # Пагинация — 12 объектов на страницу (кратно 3 колонкам)
    paginator = Paginator(queryset,  PROPERTIES_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'properties/crm/list.html', {
        'properties': page_obj,
        'page_obj': page_obj,
        'form': form,
        'total_count': total_count,
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
            # шаблонные характеристики для нового объекта
            for key in FEATURE_TEMPLATES:
                PropertyFeature.objects.get_or_create(
                    property=property_obj,
                    key=key,
                    defaults={'value': ''},
                )

            messages.success(request, 'Объект успешно создан.')
            return redirect('properties:edit', pk=property_obj.pk)
        else:
            messages.error(
                request,
                'Не удалось сохранить объект — проверьте выделенные поля.'
            )

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
        feature_formset = PropertyFeatureFormSet(
            request.POST,
            instance=property_obj,
        )
        if form.is_valid() and feature_formset.is_valid():
            form.save()
            feature_formset.save()
            messages.success(request, 'Объект успешно обновлён.')
            return _redirect_to_list_at(request, property_obj)
        else:
            messages.error(
                request,
                'Не удалось сохранить объект — проверьте выделенные поля.'
            )

    else:
        form = PropertyForm(instance=property_obj)
        feature_formset = PropertyFeatureFormSet(instance=property_obj)

    return render(request, 'properties/crm/form.html', {
        'form': form,
        'property': property_obj,
        'feature_formset': feature_formset,
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


@crm_required
def property_export_excel(request):
    """Экспорт объектов недвижимости в Excel."""
    # Берём тот же queryset что и в списке
    queryset = _base_queryset(request.user).select_related('agent')

    # Применяем фильтры если есть
    status = request.GET.get('status')
    deal_type = request.GET.get('deal_type')
    city = request.GET.get('city')

    if status:
        queryset = queryset.filter(status=status)
    if deal_type:
        queryset = queryset.filter(deal_type=deal_type)
    if city:
        queryset = queryset.filter(city__icontains=city)

    from datetime import datetime
    filename = f"objects_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    wb, ws, response = create_excel_response(filename)

    ws.title = 'Объекты недвижимости'

    # Заголовки
    headers = [
        '№', 'Тип сделки', 'Тип объекта', 'Статус',
        'Город', 'Район', 'Улица', 'Дом',
        'Комнат', 'Площадь общ.', 'Площадь жил.', 'Площадь кухни',
        'Этаж', 'Этажей в доме',
        'Цена, ₽', 'Цена за м², ₽',
        'Комиссия, %', 'Комиссия фикс., ₽',
        'Опубликован', 'Эксклюзив',
        'Риелтор', 'Дата создания',
    ]
    style_header_row(ws, headers)

    # Данные
    for i, prop in enumerate(queryset, 1):
        ws.append([
            i,
            prop.get_deal_type_display(),
            prop.get_property_type_display(),
            prop.get_status_display(),
            prop.city,
            prop.district or '',
            prop.street or '',
            prop.building or '',
            prop.rooms_count or '',
            float(prop.area_total) if prop.area_total else '',
            float(prop.area_living) if prop.area_living else '',
            float(prop.area_kitchen) if prop.area_kitchen else '',
            prop.floor or '',
            prop.floors_total or '',
            float(prop.price),
            float(prop.price_per_sqm) if prop.price_per_sqm else '',
            float(prop.commission_percent) if prop.commission_percent else '',
            float(prop.commission_fixed) if prop.commission_fixed else '',
            'Да' if prop.is_published else 'Нет',
            'Да' if prop.is_exclusive else 'Нет',
            prop.agent.get_full_name() if prop.agent else '',
            prop.created_at.strftime('%d.%m.%Y') if prop.created_at else '',
        ])

    return finalize_excel(wb, ws, response, start_row=2, col_count=len(headers))