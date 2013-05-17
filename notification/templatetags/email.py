from django.template.loader import render_to_string
from django.template import Library, RequestContext, Context, loader
from pinry.pins.forms import PinForm

register = Library()

@register.inclusion_tag('email/templatetags/email_header_generic.html', takes_context=True)
def header_generic(context, request):
    return context

@register.inclusion_tag('email/templatetags/email_footer_generic.html', takes_context=True)
def footer_generic(context, request):
    return context    