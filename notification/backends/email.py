# Django
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from django.core.urlresolvers import reverse
from django.template import Context
from django.template.loader import render_to_string
from django.utils.translation import ugettext

# Django Apps
from django.contrib.sites.models import Site

# This app
from notification import backends


class EmailBackend(backends.BaseBackend):
    spam_sensitivity = 2

    def can_send(self, user, notice_type):
        can_send = super(EmailBackend, self).can_send(user, notice_type)
        if can_send and user.email:
            return True
        return False

    def deliver(self, recipient, sender, notice_type, extra_context):

        context = Context(extra_context)
        
        short = backends.format_notification("short.txt",
                                             notice_type.label,
                                             context).rstrip('\n').rstrip('\r')

        message_txt = backends.format_notification("full.txt",
                                                   notice_type.label,
                                                   context)

        message = backends.format_notification("full.html",
                                               notice_type.label,
                                               context)

        body = render_to_string(("notification/email_body.html",
                                 "notification/default/email_body.html"),
                                {"message": message}, context)

        context.autoescape = False
        subject = render_to_string(("notification/email_subject.txt",
                                    "notification/default/email_subject.txt"),
                                  {"message": short}, context).rstrip('\n').rstrip('\r')
        body_txt = render_to_string(("notification/default/email_body.txt",
                                     "notification/email_body.html"),
                                    {"message": message_txt}, context)

        msg = EmailMultiAlternatives(subject, body_txt,
                settings.DEFAULT_FROM_EMAIL, [recipient.email])

        msg.attach_alternative(body, "text/html")
        msg.send()
