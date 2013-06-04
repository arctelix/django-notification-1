# Python Core
from datetime import datetime, timedelta

# Django
from django.core.urlresolvers import reverse
from django.core.signing import Signer, BadSignature
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404, render
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.db.models import Q
from django.contrib import messages
from django.core.urlresolvers import resolve, Resolver404

# Django Apps
from django.contrib.auth.decorators import login_required

# This app
#FIXME dinamically import this
from notification.backends.website import Notice
from notification.models import (NoticeType, NoticeSetting, NOTICE_MEDIA,
                                 get_notification_setting)

@login_required
def notices(request, alln=False, archived=False):
    """
    The main notices index view.
    """
    notices = Notice.objects.notices_for(request.user, archived)
    
    # TODO:for date grouper but i'm sure there is a better way.
    this_month = datetime.now().strftime("%B %Y")
    this_week = datetime.now().strftime("%W %Y")
    today = datetime.now().strftime("%j %Y")
    
    week_ago = datetime.now() - timedelta(weeks=1)

    if not alln:
        old = datetime.now() - timedelta(days=3)
        latest_notices = notices.filter(Q(unseen=True) |
                                        Q(added__gt=old))

        if len(latest_notices) < 10:
            latest_notices = notices.filter()[:10]

        notices = latest_notices
    
    return render_to_response("notification/notices.html", {
        "notices": notices,
        "archived": archived,
        'all': alln,
        'this_month': this_month,
        'this_week': this_week,
        'today': today,
        'week_ago': week_ago,
    }, context_instance=RequestContext(request))

@login_required
def notice_settings(request):
    """
    The notice settings view.

    Template: :template:`notification/notice_settings.html`

    Context:

        notice_types
            A list of all :model:`notification.NoticeType` objects.

        notice_settings
            A dictionary containing ``column_headers`` for each ``NOTICE_MEDIA``
            and ``rows`` containing a list of dictionaries: ``notice_type``, a
            :model:`notification.NoticeType` object and ``cells``, a list of
            tuples whose first value is suitable for use in forms and the second
            value is ``True`` or ``False`` depending on a ``request.POST``
            variable called ``form_label``, whose valid value is ``on``.
    """
    notice_types = NoticeType.objects.all()
    settings_table = []
    changed = False
    for notice_type in notice_types:
        settings_row = []
        for medium_id, medium_display in NOTICE_MEDIA:
            form_label = "%s_%s" % (notice_type.label, medium_id)
            setting = get_notification_setting(request.user,
                                               notice_type,
                                               medium_id)
            if request.method == "POST":
                if request.POST.get(form_label) == "on":
                    if not setting.send:
                        setting.send = True
                        setting.save()
                        changed = True
                else:
                    if setting.send:
                        setting.send = False
                        setting.save()
                        changed = True
            settings_row.append((form_label, setting.send))
        #use to determin if a notice_type is from the system or a system user
        notice_type.is_system = notice_type.label.find('system')+1
        settings_table.append({"notice_type": notice_type, "cells": settings_row})

    if changed:
        messages.add_message(request, messages.INFO, "Notification settings updated.")

    if request.method == "POST":
        next_page = request.POST.get("next_page", ".")
        return HttpResponseRedirect(next_page)

    notice_settings = {
        "column_headers": [medium_display for medium_id, medium_display in NOTICE_MEDIA],
        "rows": settings_table,
    }

    return render_to_response("notification/notice_settings.html", {
        "notice_types": notice_types,
        "notice_settings": notice_settings,
    }, context_instance=RequestContext(request))


@login_required
def single(request, id, mark_seen=True):
    """
    Detail view for a single :model:`notification.Notice`.

    Template: :template:`notification/single.html`

    Context:

        notice
            The :model:`notification.Notice` being viewed

    Optional arguments:

        mark_seen
            If ``True``, mark the notice as seen if it isn't
            already.  Do nothing if ``False``.  Default: ``True``.
    """
    notice = get_object_or_404(Notice, id=id)
    if request.user == notice.recipient:
        if mark_seen and notice.unseen:
            notice.unseen = False
            notice.save()
        return render_to_response("notification/single.html", {
            "notice": notice,
        }, context_instance=RequestContext(request))
    raise Http404
    
@login_required
def view_sender(request, id, sender_url=None, mark_seen=True):
    """
    Use in a template to generate a link to the sender's url and mark the notice as seen.

    Optional arguments:
    
        sender_url
            If not specified as a url perameter then the view will attempt to
            generate a url based on the notice.content_type & notice.sender.id.
            IF your url's are designed to mirror your model names this shold work.
            Otherwise sepicfy the url you would like to redirect to as a get perameter
            IE: {% url notification_view_sender notice.id %}?sender_url=/some/redirect/url/
        mark_seen
            If ``True``, mark the notice as seen if it isn't
            already.  Do nothing if ``False``.  Default: ``True``.
    """
    notice = get_object_or_404(Notice, id=id)
    if request.user == notice.recipient:
        if mark_seen and notice.unseen:
            notice.unseen = False
            notice.save()
        if not sender_url:
            sender_url = request.REQUEST.get('sender_url',None)
            try:
                resolve(sender_url)
            except:
                sender_url = None
        if not sender_url:
            sender_url = '/'+str(notice.content_type)+'/'+str(notice.sender.id)+'/'
            try:
                resolve(sender_url)
            except:
                print '***notifications.views.view_sender: not valid url: ', sender_url
                raise Http404
        
        return HttpResponseRedirect(sender_url)
    
    messages.add_message(request, messages.ERROR, "This was not your notification!")
    raise Http404


@login_required
def toggle_archived(request, noticeid=None, next_page=None):
    """
    Archive a :model:`notices.Notice` if the requesting user is the
    recipient or if the user is a superuser.  Returns a
    ``HttpResponseRedirect`` when complete.

    Optional arguments:

        noticeid
            The ID of the :model:`notices.Notice` to be archived.

        next_page
            The page to redirect to when done.
    """
    if not next_page:
        next_page = request.META['HTTP_REFERER']
    if noticeid:
        try:
            notice = Notice.objects.get(id=noticeid)
            if request.user == notice.recipient or request.user.is_superuser:
                if notice.archived:
                    notice.archived = False
                    notice.save()
                else:
                    notice.archived = True
                    notice.save()
            else:   # you can archive other users' notices
                    # only if you are superuser.
                return HttpResponseRedirect(next_page)
        except Notice.DoesNotExist:
            return HttpResponseRedirect(next_page)
    return HttpResponseRedirect(next_page)


@login_required
def delete(request, noticeid=None, next_page=None):
    """
    Delete a :model:`notices.Notice` if the requesting user is the recipient
    or if the user is a superuser.  Returns a ``HttpResponseRedirect`` when
    complete.

    Optional arguments:

        noticeid
            The ID of the :model:`notices.Notice` to be archived.

        next_page
            The page to redirect to when done.
    """
    if not next_page:
        next_page = request.META['HTTP_REFERER']
    if noticeid:
        try:
            notice = Notice.objects.get(id=noticeid)
            if request.user == notice.recipient or request.user.is_superuser:
                notice.delete()
            else:   # you can delete other users' notices
                    # only if you are superuser.
                return HttpResponseRedirect(next_page)
        except Notice.DoesNotExist:
            return HttpResponseRedirect(next_page)
    return HttpResponseRedirect(next_page)


@login_required    
def toggle_unseen(request, noticeid=None, next_page=None):
    """
    Toggle unseen :model:`notices.Notice` if the requesting user is the recipient
    or if the user is a superuser.  Returns a ``HttpResponseRedirect`` when
    complete.

    Optional arguments:

        noticeid
            The ID of the :model:`notices.Notice` to be archived.

        next_page
            The page to redirect to when done.
            Defaut is HTTP_REFERER
    """
    if not next_page:
        next_page = request.META['HTTP_REFERER']
    if noticeid:
        try:
            notice = Notice.objects.get(id=noticeid)
            if request.user == notice.recipient or request.user.is_superuser:
                if notice.unseen:
                    notice.unseen = False
                    notice.save()
                else:
                    notice.unseen = True
                    notice.save()
            else:   # you can delete other users' notices
                    # only if you are superuser.
                return HttpResponseRedirect(next_page)
        except Notice.DoesNotExist:
            return HttpResponseRedirect(next_page)
    return HttpResponseRedirect(next_page)


@login_required    
def toggle_all(request, next_page=None):
    """
    Toggles: delete, archived, & unseen as checked in form: model:`notices.Notice` if the requesting user is the recipient
    or if the user is a superuser.  Returns a ``HttpResponseRedirect`` when
    complete.

    Optional arguments:
        next_page
            The page to redirect to when done.
            Defaut is HTTP_REFERER
    """
    if not next_page:
        next_page = request.META['HTTP_REFERER']
    notices = {}
    for var in request.POST:
        if var != 'csrfmiddlewaretoken':
            svar = var.split('-')
            id = svar[0]
            action = svar[1]
            value = request.POST[var]
            if value == 'True': value = True
            if value == 'False': value = False
            if not notices.get(id, False):
                notices[id] = {action:value}
            else:
               notices[id].update({action:value})
    for notice_id in notices:
        try:
            notice = Notice.objects.get(id=notice_id)
            if request.user == notice.recipient or request.user.is_superuser:
                if notices[notice_id].get('unseen', None) != None and notice.unseen != notices[notice_id]['unseen']:
                    notice.unseen = notices[notice_id]['unseen']
                    notice.save()
                if notices[notice_id].get('archived', None) != None and notice.archived != notices[notice_id]['archived']:
                    notice.archived = notices[notice_id]['archived']
                    notice.save()
                if notices[notice_id].get('delete', None) != None and notices[notice_id]['delete']:
                    notice.delete()
                
            else:   # you can delete other users' notices
                    # only if you are superuser.
                return HttpResponseRedirect(next_page)
        except Notice.DoesNotExist:
            return HttpResponseRedirect(next_page)

    return HttpResponseRedirect(next_page)


@login_required
def mark_all_seen(request):
    """
    Mark all unseen notices for the requesting user as seen.  Returns a
    ``HttpResponseRedirect`` when complete. 
    """

    for notice in Notice.objects.notices_for(request.user, unseen=True):
        notice.unseen = False
        notice.save()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def unsubscribe(request, medium, code):
    signer = Signer()
    try:
        user = User.objects.get(id=signer.unsign(code))
        medium_code = [x for x in NOTICE_MEDIA if x[1] == medium][0][0]
    except (BadSignature, User.DoesNotExist, IndexError):
        raise Http404

    for ns in NoticeSetting.objects.filter(user=user, medium=medium_code):
        ns.send = False
        ns.save()

    if medium == 'email':
        ctx = {'message': """Your email address (%s) will no longer receive any
                          other email notification from us.""" % user.email}

    return render(request, 'notification/unsubscribed.html', ctx)

from django.contrib.contenttypes.models import ContentType
from notification.models import Observation, is_observing
@login_required
def observation_settings(request, content_type_name=None):
    """
    The observation settings view.

    Template: :template:`notification/observation_settings.html`

    Context:

        notice_types
            A list of all :model:`notification.NoticeType` objects.

        notice_settings
            A dictionary containing ``column_headers`` for each ``NOTICE_MEDIA``
            and ``rows`` containing a list of dictionaries: ``notice_type``, a
            :model:`notification.NoticeType` object and ``cells``, a list of
            tuples whose first value is suitable for use in forms and the second
            value is ``True`` or ``False`` depending on a ``request.POST``
            variable called ``form_label``, whose valid value is ``on``.
    """
    if content_type_name:
        content_type = ContentType.objects.get(name=content_type_name)
        observations = Observation.objects.filter(user=request.user, content_type=content_type).order_by('object_id')
    else:
        observations = Observation.objects.filter(user=request.user).order_by('content_type', '-object_id')
    notice_types_u = [x[0] for x in set(observations.values_list('notice_type'))]
    notice_types = NoticeType.objects.filter(id__in=notice_types_u)
    observations_u = set(observations.values_list('content_type', 'user', 'object_id'))
    observer = request.user
    
    settings_table = []
    changed = False

    for observed in observations_u:
        settings_row = []
        observed_set = observations.filter(content_type=observed[0], user=observed[1], object_id=observed[2])
        for notice_type in notice_types:
            try:
                qs = observed_set.filter(notice_type=notice_type)
                observed_obj = qs[0]
                form_label = "%s_%s" % (notice_type.label, observed_obj.id)
                send = observed_obj.send
                if request.method == "POST":
                    if request.POST.get(form_label) == "on":
                        if not send:
                            observed_obj.send = True
                            changed = True
                            observed_obj.save()
                    else:
                        if send:
                            observed_obj.send = False
                            changed = True
                            observed_obj.save()
                settings_row.append((form_label, observed_obj.send))
            except:
                settings_row.append((False, False))
        settings_table.append({"observed": observed_obj, "cells": settings_row})

    if changed:
        messages.add_message(request, messages.INFO, "Notification settings updated.")

    if request.method == "POST":
        next_page = request.POST.get("next_page", ".")
        return HttpResponseRedirect(next_page)

    notice_settings = {
        "column_headers": [notice_type.display for notice_type in notice_types],
        "rows": settings_table,
    }

    return render_to_response("notification/observation_settings.html", {
        "notice_types": notice_types,
        "notice_settings": notice_settings,
    }, context_instance=RequestContext(request))