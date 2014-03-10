# Python Core
from datetime import datetime, timedelta

# Django
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse

# Django Apps
from django.contrib.sites.models import Site
from django.utils.timezone import * 

# PickleField
from picklefield.fields import PickledObjectField

# This app
from notification import backends
from notification.models import NoticeType
from django.conf import settings


class NoticeManager(models.Manager):

    def notices_for(self, user, archived=False, unseen=None):
        """
        returns Notice objects for the given user.
        archived : { False: only messages not archived, True: all messages }
        unseen : {None: all notices, True: only unseen, False: only seen}
        """
        qs = self.filter(recipient=user)
        qs = qs.filter(archived=archived)
        if unseen is not None:
            qs = qs.filter(unseen=unseen)
        return qs

    def mark_read(self, sender, receiver):
        '''
        Marks all notifications emitted by the sender to the receiver as read.
        This function is tipically called when the receiver views the sender,
        so the notification about the sender isn't "fresh" anymore.
        '''
        if receiver.is_anonymous():
            return
        ctype = ContentType.objects.get_for_model(sender)
        for n in self.filter(content_type=ctype, object_id=sender.id,
                             recipient=receiver):
            n.unseen = False
            n.save()

    def unseen_count_for(self, recipient, **kwargs):
        """
        returns the number of unseen notices for the given user.
        """
        return self.notices_for(recipient, unseen=True, **kwargs).count()


# prevent error on initial syncdb for apps that incorporate django-notification-automated
try:
    #constants for sender url
    current_site = Site.objects.get_current()
    root_url = "http://%s" % unicode(current_site)
except:
    from django.db import connection
    connection.close()



class Notice(models.Model):
    '''
    A represents a notification object to be used with the website backend.
    '''
    recipient = models.ForeignKey(User, verbose_name=_("recipient"))
    notice_type = models.ForeignKey(NoticeType, verbose_name=_("notice type"))
    added = models.DateTimeField(_("added"), auto_now_add=True)
    unseen = models.BooleanField(_("unseen"), default=True)
    archived = models.BooleanField(_("archived"), default=False)

    data = PickledObjectField()

    # Polymorphic relation to allow any object to be the sender
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    sender = generic.GenericForeignKey("content_type", "object_id")

    objects = NoticeManager()

    def __unicode__(self):
        return self.notice_type.display

    def archive(self):
        self.archived = True
        self.save()
        
    def get_context(self):
        """
        website specific context for use in all templates when website is present
        """
        return  {  "added": self.added,
                   "unseen": self.unseen,
                   "archived": self.archived,
                   "content_type": self.content_type,#remove this
                   "sender_type": self.content_type.name, 
                   "object_id": self.object_id,
                   "notice_id": self.id,
                }
                
    def get_sender_url(self):
        '''
        sender_url: a path to the sender. If not specified in extra_context then a url 
        will be generated automatically (/content_type/sender.id/) if your url's are the 
        same as your model names this should work.  If the website backend is present
        then the sender_url will pass through view_sender view and mark the notice as seen.
        *If specified in extra_context, provide just the path and it will be converted to
        the proper url automatically.
        '''
        sender_path = self.data.get('sender_path', '')
        view_sender_url = reverse('notification_view_sender',args=[str(self.id)])+'?sender_url='
        
        sender_url = view_sender_url+sender_path

        return sender_url
        
        
    def render(self, template='website.html'):
        """
        Render the notification with the given template.
        """

        if not self.data: self.data = {}
        
        #provide context to replicate context provided by notification.send() for all templates
        self.data.update({  "recipient": self.recipient, 
                            "sender": self.sender,  
                            "notice": self.notice_type,
                            "root_url": root_url,
                            "sender_url": self.get_sender_url(),
                        })
        #provide website specific context
        self.data.update(self.get_context())
        
        context = self.data
        
        short = backends.format_notification("short.txt",
                                             self.notice_type.label,
                                             context).rstrip('\n')

        full = backends.format_notification("full.txt",
                                                   self.notice_type.label,
                                                   context)

        full_html = backends.format_notification("full.html",
                                               self.notice_type.label,
                                               context)
        
        #provide website template specific context
        self.data.update({  'message_short':short, 
                            'message_full':full,
                            'message_full_html':full_html,
                        })
                        
        return backends.format_notification(template,
                                            self.notice_type.label,
                                            context)
        
    def is_unseen(self):
        """
        returns value of self.unseen but also changes it to false.

        Use this in a template to mark an unseen notice differently the first
        time it is shown.
        """
        unseen = self.unseen
        if unseen:
            self.unseen = False
            self.save()
        return unseen

    class Meta:
        app_label = 'notification'  # needed for syncdb
        ordering = ["-added"]
        verbose_name = _("notice")
        verbose_name_plural = _("notices")


class WebsiteBackend(backends.BaseBackend):
    """
    Stores the notification on the website, they will be shown when the user
    visit the proper notification page.
    """
    spam_sensitivity = 1

    def deliver(self, recipient, sender, notice_type, extra_context):
        """
        Just saves the notification to the database, it gets displayed
        """
        Notice.objects.create(recipient=recipient,
                              sender=sender,
                              data=extra_context,
                              notice_type=notice_type)
