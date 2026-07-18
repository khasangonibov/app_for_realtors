from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Получить значение из словаря по ключу в шаблоне.
    Использование: {{ my_dict|get_item:key }}
    """
    return dictionary.get(str(key), '—')