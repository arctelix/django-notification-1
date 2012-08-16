# Django
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

# PickleField
from picklefield.fields import PickledObjectField

# This app
from notification import backends
from notification.models import NoticeType


class NoticeManager(models.Manager):

    def notices_for(self, user, archived=False, unseen=None):
        """
        returns Notice objects for the given user.
        archived : { False: only messages not archived, True: all messages }
        unseen : {None: all notices, True: only unseen, False: only seen}
        """
        qs = self.filter(recipient=user)
        if not archived:
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


class Notice(models.Model):
    '''
    A represents a notification object to be used with the website backend.
    '''
    recipient = models.ForeignKey(User, verbose_name=_("recipient"))
    notice_type = models.ForeignKey(NoticeType, verbose_name=_("notice type"))
    added = models.DateTimeField(_("added"), auto_now=True)
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

    def render(self, template='website.html'):
        """
        Render the notification with the given template.
        """
        self.data.update({'self': self})
        return backends.format_notification(template,
                                            self.notice_type.label,
                                            self.data)

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
