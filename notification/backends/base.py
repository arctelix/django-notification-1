class BaseBackend(object):
    """
    The base backend.
    """
    def __init__(self, medium_id, spam_sensitivity=None):
        self.medium_id = medium_id
        if spam_sensitivity is not None:
            self.spam_sensitivity = spam_sensitivity
    
    def can_send(self, user, notice_type):
        """
        Determines whether this backend is allowed to send a notification to
        the given user and notice_type.
        """
        from notification.models import should_send
        if should_send(user, notice_type, self.medium_id):
            return True
        return False
    
    def deliver(self, recipient, notice_type, extra_context):
        """
        Deliver a notification to the given recipient.
        """
        raise NotImplemented()
    
