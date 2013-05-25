from django.template import Library
from django.conf import settings
from django import template
from django.core.exceptions import ImproperlyConfigured
from urllib import quote
import socket
from django.contrib.contenttypes.models import ContentType

register = Library()

#email template tags
@register.assignment_tag
def dev_static_prefix():
    '''
    provide host ip address when STATIC_IP is a path and DEBUG is true(in dev env)
    inorder for email links to work.  Rturns '' when in production.  Prfix all relative
    url's with {{DEV_STATE_PREFIX}} in templates to get full url's in emails.
    '''
    try:
        static_url = getattr(settings, 'STATIC_URL')
        debug = getattr(settings, 'DEBUG')
    except:
        raise ImproperlyConfigured
    
    is_url  = static_url.find('//')+1
    if is_url and debug:
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
def key_word_to_url(desc, key_word, url):
    '''
    replace a word in a string with a hyperlink
    {% make_link string "key_word" "url" %}
    
    KEY_WORD_TO_URL_TRANSLATIONS:provide a dictionary of key_word translations.
    IE: if your key_word variable is content_type, in this example user is the 
    content_type and your desc refers to users as "blogger" {'user':'blogger'}
    '''
    map = getattr(settings, 'KEY_WORD_TO_URL_TRANSLATIONS', {})
    key_word = map.get(key_word, key_word)
    if str(key_word) in str(desc):
        link = '<a href="'+url+'">'+key_word.title()+'</a>'
        desc = link.join(desc.split(key_word))

    return desc
    
@register.simple_tag(name='sender_to_link')
def sender_to_link(desc, sender, url, allnames=True):
    '''
    replace a word in a string with a hyperlink
    {% sender_to_link "string" sender "url" allnames %}
    
    NOTIFICATION_CONTENT_TYPE_TRANSLATIONS:provide a dictionary of content_type to key_word
    translations for make_link.
    IE: if your key_word variable is content_type, in this example user is the 
    content_type and your email refers to users as "blogger" {'user':'blogger'}

    NOTIFICATION_OTHER_KEY_WORDS: Dictionary of other key words to make url's for.
    IE: if you want to replace "you" with a url pointing the the user's profile, sepcify
    {'you':'/profile/'} and the url generated witll be '/profile/user.id/'.
    
    NOTIFICATION_CHECK_FOR_SENDER_NAMES: Dictionary of sender.content_types to convert sender object name to urls.
    IE: if want user.name & blog.name to be converted to urls in notices, sepcify {'sender_type':['name_property','/url_path/']}.
    sender_type: the content_type of the sender (as a string)
    url_path: the url path to use when making the hyperlink. ie "/user/" 
    name_property: if the sender is the name you want to search the desc for. Specify None if the sender is the name
    you wnat to search for. If you want to seach for sender.user sepcify 'user'.
    url output: path to the name object's id '/url_path/name_obj.id/'
    '''
    sender_type = ContentType.objects.get_for_model(sender).name
    map = getattr(settings, 'NOTIFICATION_CONTENT_TYPE_TRANSLATIONS', {})
    sender_names = getattr(settings, 'NOTIFICATION_CHECK_FOR_SENDER_NAMES', {})
    other_key_words = getattr(settings, 'NOTIFICATION_OTHER_KEY_WORDS', {})
    desc = str(desc)
    #check for translations
    sender_type = map.get(sender_type, sender_type)
    
    #check for sender_type
    if sender_type in desc:
        link = '<a href="'+url+'">'+sender_type.title()+'</a>'
        desc = link.join(desc.split(sender_type))
    
    #also check for the sender's name if allnames=True or if sender_type in sender_names
    print 'sender_type:', sender_type
    if allnames and sender_type not in sender_names:
        #add current sender name to list
        sender_names.update({sender_type:['self','/'+sender_type+'/']})
    if allnames or allnames == None and sender_type in sender_names:
        type = sender_names[sender_type]
        url_path = type[1]
        name_property = type[0] or 'self'
        sender_name_obj = getattr(sender, name_property, sender)
        sender_name = str(sender_name_obj)
        #set up id for url
        id = ''#str(getattr(sender_name_obj,'id', ''))
        if id: id = id+'/'
        if sender_name.lower() in desc.lower():
            link = '<a href="'+url_path+id+'">'+sender_name.title()+'</a>'
            desc = link.join(desc.split(sender_name.lower()))
            desc = link.join(desc.split(sender_name.title()))
                
    #also check for other key words
    for key_word in other_key_words:
        if key_word in desc:
            link = '<a href="'+other_key_words[key_word]+str(sender.id)+'/">'+key_word.title()+'</a>'
            desc = link.join(desc.split(key_word))

    return desc

@register.assignment_tag(name='observed_desc')
def convert_to_observed_description(desc, sender_type, from_user):
    '''
    Convert a notice description to an observed description
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
