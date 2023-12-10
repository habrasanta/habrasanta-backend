from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, F
from django.db.models.functions import Coalesce

from habrasanta.celery import send_email, send_notification
from habrasanta.models import Season, Message, User, Participation


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.match_season()
        self.send_chat_notifications()

    def match_season(self, *args, **options):
        """
        Match addresses in an unmatched season with closed registration.
        """
        with transaction.atomic():
            try:
                season = Season.objects.get(
                    registration_close__lt=timezone.now(),
                    address_match=None,
                )
            except Season.DoesNotExist:
                self.stdout.write("No address matching needed")
                return # Nothing to do.
            self.stdout.write("Gonna match {}...".format(season))
            clusters = [["RU", "BY"], ["UA"], []]
            for cluster in clusters:
                participants = Participation.objects.filter(season=season).order_by("?")
                if len(cluster):
                    self.stdout.write("Gonna match cluster '{}'...".format(",".join(cluster)))
                    participants = participants.filter(country__in=cluster)
                else:
                    self.stdout.write("Gonna match default cluster...")
                if len(participants) < 3:
                    if len(participants) > 0:
                        self.stdout.write(self.style.ERROR(
                            "Not enough participants to match cluster {} in season {}!".format(",".join(cluster), season.id)
                        ))
                    return # Nothing to do.
                last = len(participants) - 1
                for i, participant in enumerate(participants):
                    if i == last:
                        giftee = participants[0]
                    else:
                        giftee = participants[i + 1]
                    # Make sure the user isn't matched to themself (happened once...)
                    assert giftee != participant
                    # TODO: Make sure the users weren't matched in another season before.
                    participant.giftee = giftee
                    participant.save()
                    transaction.on_commit(send_notification.s(
                        participant.user.id,
                        "Вам назначен получатель подарка. Посмотреть адрес можно в " +
                        "<a href=\"https://habra-adm.ru/{}/profile/\">профиле</a>.".format(season.id)
                    ).delay)
                    transaction.on_commit(send_email.s(
                        participant.user.id,
                        "пора отправлять подарок",
                        "Привет, Анонимный Дед Мороз!\n\n" +
                        "Вам назначен получатель подарка. Посмотреть адрес внука можно в профиле: " +
                        "https://habra-adm.ru/{}/profile/".format(season.id)
                    ).delay)
            season.address_match = timezone.now()
            season.save()
            self.stdout.write(self.style.SUCCESS("Season {} matched!".format(season.id)))

    def send_chat_notifications(self, *args, **options):
        """
        Find unread chat messages the users are not yet aware of and send out notifications.
        """
        with transaction.atomic():
            now = timezone.now()
            queryset = Message.objects.filter(
                read_date=None,
                send_date__gt=Coalesce(
                    F("recipient__user__last_chat_notification"),
                    now - timedelta(days=60),
                ),
            ).values("recipient__user").annotate(cnt=Count("id"))
            for result in queryset:
                plural = self.russian_plural(
                    result["cnt"],
                    "новое сообщение", # 1
                    "новых сообщения", # 2
                    "новых сообщений" # 5
                )
                transaction.on_commit(send_notification.s(
                    result["recipient__user"],
                    "Вам прислали <b>{}</b> {}".format(result["cnt"], plural) +
                    "- не тяните с прочтением, наверняка там что-то важное!"
                ).delay)
                transaction.on_commit(send_email.s(
                    result["recipient__user"],
                    "у вас <b>{}</b> {}".format(result["cnt"], plural),
                    "Приветствуем!\n\n" +
                    "Вам прислали {} {} ".format(result["cnt"], plural) +
                    "- не тяните с прочтением, наверняка там что-то важное!"
                ).delay)
                User.objects.filter(pk=result["recipient__user"]).update(last_chat_notification=now)
                self.stdout.write(self.style.SUCCESS("User {} notified".format(result["recipient__user"])))
            else:
                print("Nobody has received new messages yet")

    def russian_plural(self, n, one, few, many):
        if n % 10 == 1 and n % 100 != 11:
            return one
        if n % 10 >= 2 and n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
            return few
        return many
