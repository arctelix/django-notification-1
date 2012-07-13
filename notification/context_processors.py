from notification.backends.website import Notice

def notification(request):
    user = request.user

    if user.is_authenticated():
        return {"notice_unseen_count": Notice.objects.unseen_count_for(user)}
    else:
        return {}
