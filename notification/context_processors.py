from notification.backends.website import Notice

def notification(request):
    user = request.user

    if user.is_authenticated():
        count = Notice.objects.unseen_count_for(user)
        unseen = 'none'
        if count > 0:
            unseen = 'unseen'
        return {"notice_unseen_count": count,'notice_unseen':unseen}
    else:
        return {}
