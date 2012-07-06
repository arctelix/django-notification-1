from notification import backends
from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import get_language, activate, ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
import settings

class NoticeType(models.Model):
    '''
    Stores a Notice class. Every notification sent out must belong to a
    specific class.
    '''
    label = models.CharField(_("label"), max_length=40)
    display = models.CharField(_("display"), max_length=50)
    description = models.CharField(_("description"), max_length=100)
    # The nitice of this type will only get sent using a medium with span
    # sensitivity less than or equal than this number.
    default = models.IntegerField(_("default"))

    def __unicode__(self):
        return self.label

    class Meta:
        verbose_name = _("notice type")
        verbose_name_plural = _("notice types")


# XXX These lines must come AFTER NoticeType is defined
# key is a tuple (medium_id, backend_label)
NOTIFICATION_BACKENDS = backends.load_backends()
NOTICE_MEDIA = [key for key in NOTIFICATION_BACKENDS.keys()]
NOTICE_MEDIA_DEFAULTS = {key[0] : backend.spam_sensitivity for key,backend in \
                                                 NOTIFICATION_BACKENDS.items()}

def create_notice_type(label, display, description, default=2, verbosity=1):
    '''
    Creates a new NoticeType.
    This is intended to be used by other apps as a post_syncdb manangement step.
    '''
    try:
        notice_type = NoticeType.objects.get(label=label)
        updated = False
        if display != notice_type.display:
            notice_type.display = display
            updated = True
        if description != notice_type.description:
            notice_type.description = description
            updated = True
        if default != notice_type.default:
            notice_type.default = default
            updated = True
        if updated:
            notice_type.save()
            if verbosity > 0:
                print "Updated %s NoticeType" % label
    except NoticeType.DoesNotExist:
        NoticeType(label=label,
                   display=display,
                   description=description,
                   default=default).save()
        if verbosity > 0:
            print "Created %s NoticeType" % label

class NoticeSetting(models.Model):
    '''
    Object that indicates, for a given user, whether to send notifications
    of a given NoticeType using a given medium.
    '''

    user = models.ForeignKey(User, verbose_name=_("user"))
    notice_type = models.ForeignKey(NoticeType, verbose_name=_("notice type"))
    medium = models.CharField(_("medium"), max_length=1, choices=NOTICE_MEDIA)
    send = models.BooleanField(_("send"))

    class Meta:
        verbose_name = _("notice setting")
        verbose_name_plural = _("notice settings")
        unique_together = ("user", "notice_type", "medium")

def get_notification_setting(user, notice_type, medium):
    try:
        return NoticeSetting.objects.get(user = user,
                                         notice_type = notice_type,
                                         medium = medium)
    except NoticeSetting.DoesNotExist:
        send = NOTICE_MEDIA_DEFAULTS[medium] <= notice_type.default

        return NoticeSetting.objects.create(user = user,
                                            notice_type = notice_type,
                                            medium = medium,
                                            send = send)

def should_send(user, notice_type, medium):
    return get_notification_setting(user, notice_type, medium).send

class LanguageStoreNotAvailable(Exception):
    pass

def get_notification_language(user):
    '''
    Returns site-specific notification language for this user. Raises
    LanguageStoreNotAvailable if this site does not use translated
    notifications.
    '''
    if getattr(settings, "NOTIFICATION_LANGUAGE_MODULE", False):
        try:
            app_lbl, model_nm = settings.NOTIFICATION_LANGUAGE_MODULE.split(".")
            model = models.get_model(app_lbl, model_nm)
            language_model = model._default_manager.get(user__id__exact=user.id)
            if hasattr(language_model, "language"):
                return language_model.language
        except (ImportError, ImproperlyConfigured, model.DoesNotExist):
            raise LanguageStoreNotAvailable
    raise LanguageStoreNotAvailable

def broadcast(label, extra_context=None, sender=None, exclude=None):
    '''Brodcasts a notification for all the users on the system.'''

    extra_context = extra_context or {}
    exclude = exclude or []
    send_to = set(User.objects.all()) - set(exclude)

    send(send_to, label, extra_context, sender)

def send(users, label, extra_context={}, sender=None):
    '''
    Creates a new notice.
    This is intended to be how other apps create new notices:
    notification.send(user, "friends_invite_sent", {"foo": "bar"})
    '''
    notice_type = NoticeType.objects.get(label=label)
    current_language = get_language()

    for user in users:
        try:
            activate(get_notification_language(user))
        except LanguageStoreNotAvailable:
            pass

        for backend in NOTIFICATION_BACKENDS.values():
            if backend.can_send(user, notice_type):
                backend.deliver(user, sender, notice_type, extra_context)

    # reset environment to original language
    activate(current_language)

class ObservedItemManager(models.Manager):

    def observers(self, observed, label):
        '''
        Returns all ObservedItems for an observed object (everything obserting
        the object)
        '''
        content_type = ContentType.objects.get_for_model(observed)
        observations = self.filter(content_type=content_type,
                                   object_id=observed.id,
                                   notice_type__label=label)
        return observations

    def get_for(self, observed, observer, label):
        '''
        Returns an observation relationship between observer and observed,
        using the notification type of the given label
        '''
        content_type = ContentType.objects.get_for_model(observed)
        observation = self.get(content_type=content_type,
                               object_id = observed.id,
                               user = observer,
                               notice_type__label = label)
        return observation


class Observation(models.Model):
    '''
    This works like a many to many table, defining observation relationships 
    between observers and observed objects.
    '''
    user = models.ForeignKey(User, verbose_name=_("user"))
    notice_type = models.ForeignKey(NoticeType, verbose_name=_("notice type"))
    added = models.DateTimeField(_("added"), auto_now = True)
    objects = ObservedItemManager()
    # Polymorphic relation to allow any object to be observed
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    observed_object = generic.GenericForeignKey("content_type", "object_id") 

    class meta:
        unique_toguether = ('user', 'notice_type', 'content_type', 'object_id')

    def send_notice(self, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context.update({"observed": self.observed_object})
        send([self.user],
             self.notice_type.label,
             extra_context,
             sender = self.observed_object)

    class Meta:
        ordering = ["-added"]
        verbose_name = _("observed item")
        verbose_name_plural = _("observed items")

def observe(observed, observer, labels):
    '''
    Create a new Observation
    To be used by applications to register a user as an observer for some
    object.
    '''
    if not isinstance(labels, list):
        labels = [labels]
    for label in labels:
        if not is_observing(observed, observer, label):
            notice_type = NoticeType.objects.get(label=label)
            observed_item = Observation(user=observer,
                                        observed_object=observed,
                                        notice_type=notice_type)
            observed_item.save()

def stop_observing(observed, observer, labels):
    '''
    Remove an Observation
    '''
    if not isinstance(labels, list):
        labels = [labels]
    for label in labels:
        try:
            Observation.objects.get_for(observed, observer, label).delete()
        except Observation.DoesNotExist:
            pass

def send_observation_notices_for(observed, label, extra_context={}, 
                                 exclude=[]):
    '''
    Send a Notice for each user observing this label at the observed object.
    '''
    observations = Observation.objects.observers(observed, label)
    for observation in observations:
        if observation.user not in exclude:
            observation.send_notice(extra_context)

def is_observing(observed, observer, labels):
    if observer.is_anonymous(): return False
    if not isinstance(labels, list):
        labels = [labels]
    for label in labels:
        try:
            Observation.objects.get_for(observed, observer, label)
        except Observation.DoesNotExist:
            return False
        except Observation.MultipleObjectsReturned:
            pass
    return True

def get_observations(observer, observed_type, labels):
    if observer.is_anonymous(): return []
    if not isinstance(labels, list):
        labels = [labels]
    elements = set()
    for label in labels:
        content_type = ContentType.objects.get_for_model(observed_type)
        for x in Observation.objects.filter(user=observer,
                                            notice_type__label__in=labels,
                                            content_type=content_type):
            elements.add(x.observed_object)
    return list(elements)
