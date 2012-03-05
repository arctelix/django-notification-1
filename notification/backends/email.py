from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models.loading import get_app
from django.template import Context
from django.template.loader import render_to_string
from django.utils.translation import ugettext
from django.core.exceptions import ImproperlyConfigured

from django.contrib.sites.models import Site

from notification import backends


class EmailBackend(backends.BaseBackend):
    spam_sensitivity = 2
    
    def can_send(self, user, notice_type):
        can_send = super(EmailBackend, self).can_send(user, notice_type)
        if can_send and user.email:
            return True
        return False
        
    def deliver(self, recipient, sender, notice_type, extra_context):
        # TODO: require this to be passed in extra_context
        current_site = Site.objects.get_current()
        notices_url = u"http://%s%s" % (
            unicode(Site.objects.get_current()),
            reverse("notification_notices"),
        )
        
        # update context with user specific translations
        context = Context({
            "recipient": recipient,
            "sender": sender,
            "notice": ugettext(notice_type.display),
            "notices_url": notices_url,
            "current_site": current_site,
        })
        context.update(extra_context)
        
        short = backends.format_notification("short.txt",
                                             notice_type.label,
                                             context)
        message = backends.format_notification("full.txt",
                                               notice_type.label,
                                               context)
        
        subject = render_to_string("notification/email_subject.txt",
                                  {"message": short}, context)
        
        body = render_to_string("notification/email_body.txt",
                                {"message": message}, context)
        
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient.email])
