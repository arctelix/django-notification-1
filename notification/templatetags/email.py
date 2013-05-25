from django.template import Library
from django.conf import settings
from django import template
from django.core.exceptions import ImproperlyConfigured
from urllib import quote
import socket

register = Library()

#email template tags
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

#notice template tags
@register.simple_tag(name='make_link')
def key_word_to_link(desc, key_word, url):
    '''
    replace a word in a string with a hyperlink
    {% make_link string "key_word" "url" %}
    '''
    if str(key_word) in desc:
        link = '<a href="'+url+'">'+key_word.title()+'</a>'
        new_value = link.join(desc.split(key_word))
    else:
        new_value = 'make_link failed:', 'desc: ',desc, 'key_word: ',key_word, 'url: ',url

    return new_value

@register.assignment_tag(name='observed_desc')
def convert_to_observed_description(desc, sender_type, from_user):
    '''
    Convert a notice description to an observed description
    replace notice description with observed description
    {% observed_desc notice.description sender_type sender_url as desc %}
    {% make_link desc sender_type sender_url %}
    *desc must be of the form "has ___ on your sender_type"
    '''
    if sender_type in desc:
        owner_object = str(from_user).title()+"'s "
        desc = desc.replace('has', 'has also')
        action = desc.split('your')[0]
        new_value = action+owner_object+sender_type
    else:
        new_value = ''
    return new_value
