from habrasanta.models import Event


def log_user_login(sender, user, request, **kwargs):
    if not user:
        return
    Event.objects.create(
        typ=Event.LOGGED_IN,
        sub=user,
        ip_address=request.META["REMOTE_ADDR"],
    )


def log_user_logout(sender, user, request, **kwargs):
    if not user:
        return
    Event.objects.create(
        typ=Event.LOGGED_OUT,
        sub=user,
        ip_address=request.META["REMOTE_ADDR"],
    )
