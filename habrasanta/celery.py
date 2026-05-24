from __future__ import annotations

import logging
import os
from typing import Any

from celery import Celery, Task
from celery.exceptions import Reject
from django.conf import settings
from django.core.mail import EmailMessage

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "habrasanta.settings")

logger = logging.getLogger(__name__)

app = Celery("habrasanta")
app.config_from_object("django.conf:settings", namespace="CELERY")


@app.task(bind=True)
def send_notification(self: Task[Any, Any], user_id: int, message: str) -> None:
    from habrasanta.models import User
    from habrasanta.utils import session

    user = User.objects.get(pk=user_id)
    if not user.habr_token:
        raise Reject(f"The access token of user '{user.login}' is unknown")
    try:
        response = session.post(
            "https://habr.com/api/v2/me/notifications/list",
            data={
                "message": message,
            },
            headers={
                "client": settings.HABR_CLIENT_ID,
                "token": user.habr_token,
            },
            timeout=5,
        )
    except Exception as e:
        # Happens on timeout, DNS errors, etc.
        raise self.retry(countdown=60 * 5, exc=e) from None
    if response.status_code == 401:
        # Happens when the user revoked access to their account.
        raise Reject(
            f"Could not send notification to user '{user.login}': {response.text}"
        )
    try:
        response.raise_for_status()
    except Exception as e:
        # Happens when the connection was successful, but Habr failed.
        raise self.retry(countdown=60 * 5, exc=e) from None


@app.task(bind=True)
def send_email(self: Task[Any, Any], user_id: int, subject: str, body: str) -> int:
    from habrasanta.models import User

    user = User.objects.get(pk=user_id)
    if not user.email:
        raise Reject(f"The email address of user '{user.login}' is not known")
    if not user.email_allowed:
        raise Reject(f"User '{user.login}' has prohibited sending them emails")
    unsubscribe_url = f"https://habra-adm.ru/backend/unsubscribe?uid={user.habr_id}&token={user.email_token}"
    message = (
        "{body}\n\n"
        + "---\n\n"
        + "Мы получили этот почтовый адрес ({email}) через API Хабра, т. к. "
        + "вы входили на сайт habra-adm.ru.\n\n"
        + "Если вы не хотите получать уведомления от Хабра-АДМ, просто перейдите по ссылке: {unsubscribe_url}\n\n"
        + "Письмо может содержать конфиденциальную информацию. "
        + "Если вы получили его по ошибке, пожалуйста, сообщите об этом support@habra-adm.ru и "
        + "удалите это письмо. Спасибо! :-)"
    ).format(
        body=body,
        email=user.email,
        unsubscribe_url=unsubscribe_url,
    )
    headers = {
        "Message-ID": f"<{self.request.id}@habra-adm.ru>",
        "Reply-To": "Хабра-АДМ <support@habra-adm.ru>",
        "List-Unsubscribe": f"<{unsubscribe_url}>",
    }
    email = EmailMessage(
        "Клуб анонимных Дедов Морозов на Хабре: " + subject,
        message,
        to=[f"{user.login} <{user.email}>"],
        headers=headers,
    )
    try:
        return email.send(fail_silently=False)
    except Exception as e:
        raise self.retry(countdown=60 * 5, exc=e) from None


@app.task(bind=True)
def give_badge(self: Task[Any, Any], user_id: int) -> None:
    from habrasanta.models import User
    from habrasanta.utils import session

    user = User.objects.get(pk=user_id)
    try:
        response = session.post(
            f"https://habr.com/api/v2/users/{user.login}/add_adm_badge",
            headers={
                "client": settings.HABR_CLIENT_ID,
                "apikey": settings.HABR_APIKEY,
            },
            timeout=5,
        )
    except Exception as e:
        # Happens on timeout, DNS errors, etc.
        raise self.retry(countdown=60 * 5, exc=e) from None
    if response.status_code == 409:
        # Happens when the user already has the badge.
        raise Reject(f"Looks like user '{user.login}' already has the badge")
    if response.status_code == 404:
        # Boomburum is changing usernames again.
        boomburum = User.objects.get(login="Boomburum")
        send_email.delay(
            boomburum.id,
            "не могу выдать значок!",
            f"Пользователя '{user.login}' больше нет с нами.",
        )
        return
    try:
        response.raise_for_status()
    except Exception as e:
        # Happens when connection was successful, but Habr is boom-boom.
        raise self.retry(countdown=60 * 5, exc=e) from None
