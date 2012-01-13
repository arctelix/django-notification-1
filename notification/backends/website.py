from django.db import models
from picklefield.fields import PickledObjectField
from django.contrib.auth.models import User 
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType 
from django.contrib.contenttypes import generic
from notification.models import NoticeType
from notification import backends

class NoticeManager(models.Manager):
    
    def notices_for(self, user, archived=False, unseen=None):
        """
        returns Notice objects for the given user.
        archived : { False: only messages not archived, True: all messages } 
        unseen : {None: all notices, True: only unseen, False: only see notices}
        """
        qs = self.filter(recipient=user)
        if not archived:
            qs = qs.filter(archived=archived)
        if unseen is not None:
            qs = qs.filter(unseen=unseen)
        if on_site is not None:
            qs = qs.filter(on_site=on_site)
        return qs
    
    def unseen_count_for(self, recipient, **kwargs):
        """
        returns the number of unseen notices for the given user.
        """
        return self.notices_for(recipient, unseen=True, **kwargs).count()


class Notice(models.Model):
    '''
    A represents a notification object to be used with the website backend.
    '''
    recipient = models.ForeignKey(User, verbose_name=_("recipient"))
    notice_type = models.ForeignKey(NoticeType, verbose_name=_("notice type"))
    added = models.DateTimeField(_("added"), auto_now = True)
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
        app_label = 'notification' # needed for syncdb
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
        Notice.objects.create(recipient = recipient,
                              sender = sender,
                              data = extra_context,
                              notice_type = notice_type)

