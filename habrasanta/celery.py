import logging
import os

from celery import Celery
from celery.exceptions import Reject
from django.conf import settings
from django.core.mail import EmailMessage


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "habrasanta.settings")

logger = logging.getLogger(__name__)

app = Celery("habrasanta")
app.config_from_object("django.conf:settings", namespace="CELERY")


@app.task
def send_notification(user_id, message):
    from habrasanta.models import User
    from habrasanta.utils import session
    user = User.objects.get(pk=user_id)
    if not user.habr_token:
        raise Reject("The access token of user '{}' is unknown".format(user.login))
    try:
        response = session.post("https://habr.com/api/v2/me/notifications/list", data={
            "message": message,
        }, headers={
            "client": settings.HABR_CLIENT_ID,
            "token": user.habr_token,
        }, timeout=5)
    except Exception as e:
        # Happens on timeout, DNS errors, etc.
        raise self.retry(countdown=60 * 5, exc=e)
    if response.status_code == 401:
        # Happens when the user revoked access to their account.
        raise Reject("Could not send notification to user '{}': {}".format(user.login, response.text))
    try:
        response.raise_for_status()
    except Exception as e:
        # Happens when the connection was successful, but Habr failed.
        raise self.retry(countdown=60 * 5, exc=e)


@app.task(bind=True)
def send_email(self, user_id, subject, body):
    from habrasanta.models import User
    user = User.objects.get(pk=user_id)
    if not user.email:
        raise Reject("The email address of user '{}' is not known".format(user.login))
    if not user.email_allowed:
        raise Reject("User '{}' has prohibited sending them emails".format(user.login))
    unsubscribe_url = "https://habra-adm.ru/backend/unsubscribe?uid={uid}&token={token}".format(
        uid=user.habr_id,
        token=user.email_token,
    )
    message = (
        "{body}\n\n" +
        "---\n\n" +
        "Мы получили этот почтовый адрес ({email}) через API Хабра, т. к. " +
        "вы входили на сайт habra-adm.ru.\n\n" +
        "Если вы не хотите получать уведомления от Хабра-АДМ, просто перейдите по ссылке: {unsubscribe_url}\n\n" +
        "Письмо может содержать конфиденциальную информацию. " +
        "Если вы получили его по ошибке, пожалуйста, сообщите об этом support@habra-adm.ru и " +
        "удалите это письмо. Спасибо! :-)"
    ).format(
        body=body,
        email=user.email,
        unsubscribe_url=unsubscribe_url,
    )
    headers = {
        "Message-ID": "<{}@habra-adm.ru>".format(self.request.id),
        "Reply-To": "Хабра-АДМ <support@habra-adm.ru>",
        "List-Unsubscribe": "<{}>".format(unsubscribe_url),
    }
    email = EmailMessage(
        "Клуб анонимных Дедов Морозов на Хабре: " + subject,
        message,
        to=["{} <{}>".format(user.login, user.email)],
        headers=headers,
    )
    try:
        return email.send(fail_silently=False)
    except Exception as e:
        raise self.retry(countdown=60 * 5, exc=e)
