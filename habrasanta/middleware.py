from datetime import timedelta
from django.utils import timezone


class LastOnlineMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        now = timezone.now()
        if not request.user.is_anonymous and (
                not request.user.last_online or request.user.last_online < now - timedelta(minutes=15)):
            request.user.last_online = now
            request.user.save()
        return self.get_response(request)
