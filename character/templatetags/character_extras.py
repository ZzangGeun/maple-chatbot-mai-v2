from django import template
import json

register = template.Library()

@register.filter
def pprint(value):
    """
    JSON 형태로 예쁘게 출력하는 필터
    """
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return str(value)
