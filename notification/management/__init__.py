from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _

notice_types = getattr(settings, 'NOTICE_TYPES', [])
def create_notice_types():
    for type in notice_types:
        notification.create_notice_type(type[0],_(type[1]), _(type[2]))
    print 'notice types are now up to date'

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
    def run_create_notice_types(app, created_models, verbosity, **kwargs):
        if app == notification:
            print 'creating notice types'
            create_notice_types()
    signals.post_syncdb.connect(run_create_notice_types, sender=notification)
else:
    print "Skipping creation of NoticeTypes as notification app not found"
    
