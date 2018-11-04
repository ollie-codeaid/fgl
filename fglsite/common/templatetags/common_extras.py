from django import template

register = template.Library()


@register.inclusion_tag('common/login_header.html')
def login_header(request):
    return {'request': request}