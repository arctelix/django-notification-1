# Django
from django.contrib import admin

# This app
from notification.models import NoticeType, NoticeSetting, Observation, NoticeQueueBatch
#FIXME dinamically import classes of the type ModelAdmin and register them here
from notification.backends.website import Notice

class NoticeTypeAdmin(admin.ModelAdmin):
    list_display = ["label", "display", "description", "default"]

class NoticeSettingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "notice_type", "medium", "send"]
    
class NoticeAdmin(admin.ModelAdmin):
    list_display = ["id", "recipient", "sender", "notice_type", "data", "added", "unseen", "archived"]

class ObservationAdmin(admin.ModelAdmin):
    list_display = ["id", "content_type", "object_id", "observed_object", "user", "notice_type"]

admin.site.register(NoticeType, NoticeTypeAdmin)
admin.site.register(NoticeSetting, NoticeSettingAdmin)
admin.site.register(Notice, NoticeAdmin)
admin.site.register(Observation, ObservationAdmin)
admin.site.register(NoticeQueueBatch)
