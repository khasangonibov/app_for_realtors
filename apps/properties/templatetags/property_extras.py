from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Получить значение из словаря по ключу в шаблоне.
    Использование: {{ my_dict|get_item:key }}
    """
    return dictionary.get(str(key), '—')

@register.simple_tag(takes_context=True)
def page_url(context, page_number):
    """Ссылка на страницу списка с сохранением текущих фильтров.

    QueryDict.copy() даёт изменяемую копию, поэтому присваивание
    заменяет существующий page, а не добавляет второй —
    в отличие от request.GET.urlencode + '&page='.

    Использование: <a href="{% page_url 3 %}">
    """
    params = context['request'].GET.copy()
    params['page'] = page_number
    return f'?{params.urlencode()}'
