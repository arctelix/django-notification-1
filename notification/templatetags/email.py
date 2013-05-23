from django.template import Library
from django.conf import settings
from django import template
from django.core.exceptions import ImproperlyConfigured
import socket

register = Library()

@register.assignment_tag
def dev_static_prefix():
   
    try:
        static_url = getattr(settings, 'STATIC_URL')
    except:
        raise ImproperlyConfigured
    
    is_url  = static_url.find('//')+1
    if is_url:
        static_prefix = ''
    else:
        try:
            host_ip = socket.gethostbyname(socket.gethostname())
        except:
            host_ip = localhost
        port = getattr(settings, 'EMAIL_STATIC_HOST_PORT', '8000')
        static_prefix = 'http://'+host_ip+':'+port
    return static_prefix

@register.inclusion_tag('email/templatetags/email_header_generic.html', takes_context=True)
def header_generic(context, request):
    return context

@register.inclusion_tag('email/templatetags/email_footer_generic.html', takes_context=True)
def footer_generic(context, request):
    return context  
