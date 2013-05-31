from django.conf.urls.defaults import *

from notification.views import (notices, mark_all_seen, single,
                                notice_settings, unsubscribe, view_sender, delete, 
                                toggle_archived, toggle_unseen, toggle_all, observation_settings)

urlpatterns = patterns("",
    url(r"^$", notices, name="notification_notices"),
    url(r"^all/$", notices, {'alln': True}, name="notification_notices_all"),
    url(r"^archived/$", notices, {'archived': True}, name="notification_notices_archived"),
    url(r"^settings/$", notice_settings, name="notification_notice_settings"),
    url(r"^(\d+)/$", single, name="notification_notice"),
    url(r"^delete/(\d+)/$", delete, name="notification_delete"),
    url(r"^toggle_archived/(\d+)/$", toggle_archived, name="notification_toggle_archived"),
    url(r"^toggle_unseen/(\d+)/$", toggle_unseen, name="notification_toggle_unseen"),
    url(r"^toggle_all/$", toggle_all, name="notification_toggle_all"),
    url(r"^view/(\d+)/.?$", view_sender, name="notification_view_sender"),
    url(r"^mark_all_seen/$", mark_all_seen, name="notification_mark_all_seen"),
    url(r'^unsubscribe/(\w+)/(.+)/$', unsubscribe, name="notificaton_unsubscribe"),
    url(r'^observation_settings/(?P<content_type_name>.+)$', observation_settings, name="notificaton_observation_settings"),
)
