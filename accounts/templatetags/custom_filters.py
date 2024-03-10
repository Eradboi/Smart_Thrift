from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='format_decimal')
def format_decimal(value):
    if isinstance(value, Decimal):
        if value > 999999 and value < 9999999:
            a = str(value)[:1]
            b = str(value)[1:2] 
            c = str(value)[2:3]
            return f'{a}.{b}{c}M'
        if value > 9999999:
            a = str(value)[:1]
            b = str(value)[1:2] 
            c = str(value)[2:3]
            d = str(value)[3:4]
            return f'{a}{b}.{c}{d}M'
        elif value > 99999999:
            a = str(value)[:1]
            b = str(value)[1:2] 
            c = str(value)[2:3]
            return f'{a}{b}{c}M +'   
        return format(value, ',')
    return value

@register.filter(name='format_balance')
def format_balance(value):
    if isinstance(value, Decimal):
        return format(value, ',')
    return value


@register.filter(name='get_session_value')
def get_session_value(request, key):
    return request.session.get(key)