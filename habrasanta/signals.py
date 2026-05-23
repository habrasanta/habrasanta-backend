from django.conf import settings
from django.http import HttpRequest

from habrasanta.celery import send_email
from habrasanta.models import Event, User


def log_user_login(sender: type, user: User | None, request: HttpRequest, **kwargs: object) -> None:
    if not user:
        return
    if user.is_staff and not settings.DEBUG:
        send_email.delay(
            user.id,
            "произведен вход в ваш аккаунт",
            "Приветствуем, {}!\n\n".format(user.login) +
            "Так как у вас имеется доступ в админку Хабра-АДМ, то мы вынуждены проинформировать вас о новом входе под вашим аккаунтом:\n\n" +
            "IP-адрес: {}\n".format(request.META.get("HTTP_X_REAL_IP")) +
            "User-Agent: {}\n\n".format(request.META.get("HTTP_USER_AGENT", "неизвестен")) +
            "Если это были не вы, просьба немедленно сообщить kafeman'у."
        )
    Event.objects.create(
        typ=Event.LOGGED_IN,
        sub=user,
        ip_address=request.META.get("HTTP_X_REAL_IP"),
    )


def log_user_logout(sender: type, user: User | None, request: HttpRequest, **kwargs: object) -> None:
    if not user:
        return
    Event.objects.create(
        typ=Event.LOGGED_OUT,
        sub=user,
        ip_address=request.META.get("HTTP_X_REAL_IP"),
    )
