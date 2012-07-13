# Django
from django.contrib import admin

# This app
from notification.models import NoticeType, NoticeSetting, Observation
#FIXME dinamically import classes of the type ModelAdmin and register them here
from notification.backends.website import Notice

class NoticeTypeAdmin(admin.ModelAdmin):
    list_display = ["label", "display", "description", "default"]

class NoticeSettingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "notice_type", "medium", "send"]

admin.site.register(NoticeType, NoticeTypeAdmin)
admin.site.register(NoticeSetting, NoticeSettingAdmin)
admin.site.register(Notice)
admin.site.register(Observation)
