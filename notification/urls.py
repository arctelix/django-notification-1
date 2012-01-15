from django.conf.urls.defaults import *

from notification.views import notices, mark_all_seen, single, notice_settings
#from notification.views import feed_for_user

urlpatterns = patterns("",
    url(r"^$", notices, name="notification_notices"),
    url(r"^settings/$", notice_settings, name="notification_notice_settings"),
    url(r"^(\d+)/$", single, name="notification_notice"),
    url(r"^mark_all_seen/$", mark_all_seen, name="notification_mark_all_seen"),
    #url(r"^feed/$", feed_for_user, name="notification_feed_for_user"),
)
