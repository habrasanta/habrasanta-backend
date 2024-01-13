import random

from django.core.management.base import BaseCommand

from habrasanta.celery import send_email, send_notification
from habrasanta.models import Season, Participation


INTROS = [
    "Дед Мороз, на Хабре рос,\nБорода админа,\nТы подарки нам принёс,\nЛенивая скотина?",
    "Дед Мороз, на Хабре рос,\nБорода админа,\nТы подарки всем принёс\nИли кто-то мимо?",
]

VERSES = [
    "Ждёт айтишник за компом,\nЖдёт админ за сервером,\nОтложил ты на потом,\nХрен и падла с севера.",
    "Ждёт айтишник за компом,\nЖдёт админ за сервером,\nОтложил ты на потом\nВручение бестселлера.",
    # "Ждёт айтишник за компом,\nЖдёт админ за сервером,\nВ нашем клубе непростом,\nБудешь главным дураком.",
]

OUTROS = [
    "Срочно почте передай\nЦенный свой подарок,\nА иначе прям мастдай,\nСтарый ты огарок!",
    "Срочно почте передай\nСвой подарок ценный,\nА иначе прям мастдай\nБудет техногенный.",
    "Срочно почте передай\nСвой подарок ценный,\nА иначе ай-ай-ай\nБудет техногенный.",
    "Срочно почте передай\nСвой подарок важный,\nНу и внуку пожелай\nПрод катить безбажный.",
]

PS = "P.S. Если возникли какие-то проблемы с отправкой, напишите Boomburum на Хабре или в Telegram."


class Command(BaseCommand):
    def handle(self, *args, **options):
        season = Season.objects.latest()
        assert not season.is_closed
        for participant in Participation.objects.filter(season=season, gift_shipped_at=None):
            text = "\n\n".join([random.choice(INTROS), random.choice(VERSES), random.choice(OUTROS), PS])
            send_notification.delay(participant.user.id, text)
            send_email.delay(participant.user.id, "не забудьте отправить подарок", text)
