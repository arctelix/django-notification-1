from django.template import Library
from django.conf import settings
from notification.models import NoticeType, get_notification_setting, NOTICE_MEDIA

register = Library()

@register.assignment_tag(takes_context=True)
def notification_settings(context):
    '''
    Provide users notification settings for custom template rendering.
    '''
    user = context['request'].user
    user_settings = []
    if user.is_authenticated():
        notice_types = NoticeType.objects.all()
        for notice in notice_types:
            for media in NOTICE_MEDIA:
                setting = get_notification_setting(user, notice, media[0])
                #setting.send = 'yes' if setting.send else ''
                user_settings.append(setting)
    return user_settings