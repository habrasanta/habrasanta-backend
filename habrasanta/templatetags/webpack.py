from django import template
from django.conf import settings


register = template.Library()


@register.simple_tag
def webpack_asset(name, key):
    return settings.WEBPACK[name][key]
