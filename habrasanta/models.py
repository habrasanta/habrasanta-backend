import secrets

from django_countries.fields import CountryField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from functools import partial

from habrasanta.utils import fetch_habr_profile


class User(models.Model):
    # TODO: UPPER() index
    login = models.CharField(max_length=25, unique=True, editable=False, db_column="username")

    email = models.CharField(max_length=128, null=True, editable=False)
    email_allowed = models.BooleanField("e-mail уведомления", default=True, editable=False)
    email_token = models.CharField(default=partial(secrets.token_urlsafe, 24), editable=False, max_length=32)

    habr_id = models.CharField(null=True, max_length=128, unique=True, editable=False)
    habr_token = models.CharField(null=True, max_length=40, editable=False)

    is_banned = models.BooleanField("забанен", default=False, editable=False)

    first_login = models.DateTimeField("первый вход", default=timezone.now, editable=False)
    last_login = models.DateTimeField("последний вход", default=timezone.now, null=True, editable=False)
    last_online = models.DateTimeField("последний online", default=timezone.now, null=True, editable=False)
    last_chat_notification = models.DateTimeField("последнее уведомление о новых сообщениях", blank=True, null=True, editable=False)

    USERNAME_FIELD = "login"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        permissions = [
            ("view_user_email", "Может просматривать e-mail адрес пользователя"),
        ]

    def __str__(self):
        return self.login

    @property
    def is_active(self):
        return True

    @property
    def is_staff(self):
        return self.login in settings.HABRASANTA_ADMINS

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    def has_module_perms(self, package_name):
        # Hide default auth app from Django admin.
        if package_name == "auth":
            return False
        return self.is_staff

    def has_perm(self, perm, obj=None):
        # No one can change events.
        if perm == "habrasanta.change_event":
            return False
        # No one can delete events.
        if perm == "habrasanta.delete_event":
            return False
        # No one can add events manually.
        if perm == "habrasanta.add_event":
            return False
        # No one can add participations manually.
        if perm == "habrasanta.add_participation":
            return False
        # No one can delete participations manually.
        if perm == "habrasanta.delete_participation":
            return False
        # Only Habr has permission to create users.
        if perm == "habrasanta.add_user":
            return False
        # Don't allow to delete users too (at least for now...)
        if perm == "habrasanta.delete_user":
            return False
        # Only kafeman and the user itself can access personal information.
        if perm == "habrasanta.view_participation_address":
            return self.login == "kafeman" or obj.user == self
        # Only kafeman and the user itself can access email addresses.
        if perm == "habrasanta.view_user_email":
            return self.login == "kafeman" or obj == self
        # Only celery can store task results.
        if perm == "django_celery_results.add_taskresult":
            return False
        # Only celery can change task results.
        if perm == "django_celery_results.change_taskresult":
            return False
        return self.is_staff

    def get_username(self):
        return self.login

    @property
    def profile(self):
        if not hasattr(self, "_profile"):
            self._profile = fetch_habr_profile(self.login)
        return self._profile

    @property
    def karma(self):
        return self.profile["karma"]

    @property
    def avatar_url(self):
        url = self.profile["avatar_url"]
        if not url:
            return "https://hsto.org/storage/habrastock/i/avatars/stub-user-middle.gif"
        return url

    @property
    def is_readonly(self):
        return self.profile["is_readonly"]

    @property
    def has_badge(self):
        return self.profile["has_badge"]

    @property
    def can_participate(self):
        return not self.is_banned and not self.is_readonly and (
            self.karma >= settings.HABRASANTA_KARMA_LIMIT or self.has_badge)


class Season(models.Model):
    id = models.PositiveIntegerField("ID", primary_key=True)

    registration_open = models.DateTimeField("открытие регистрации")
    registration_close = models.DateTimeField("закрытие регистрации")
    address_match = models.DateTimeField("жеребьевка адресов", editable=False, null=True,
        help_text="Устанавливается скриптом жеребьевки автоматически")
    season_close = models.DateTimeField("закрытие сезона")

    member_count = models.PositiveIntegerField(default=0, editable=False)
    shipped_count = models.PositiveIntegerField(default=0, editable=False)
    delivered_count = models.PositiveIntegerField(default=0, editable=False)

    gallery_url = models.URLField("пост хвастовства подарками", blank=True)

    users = models.ManyToManyField(User, related_name="seasons", through="Participation")

    class Meta:
        get_latest_by = "id"
        verbose_name = "сезон"
        verbose_name_plural = "сезоны"

    def __str__(self):
        return "АДМ {}".format(self.id)

    @property
    def is_closed(self) -> bool:
        return timezone.now() > self.season_close

    @property
    def is_registration_open(self) -> bool:
        if self.address_match:
            return False
        now = timezone.now()
        return now >= self.registration_open and now < self.registration_close

    @property
    def is_matched(self) -> bool:
        return self.address_match is not None

    def clean(self):
        error_dict = {}
        if self.registration_close < self.registration_open:
            error_dict["registration_close"] = "Регистрация не может закрыться до открытия"
        if self.season_close < self.registration_close:
            error_dict["season_close"] = "Сезон не может закончиться до закрытия регистрации"
        if len(error_dict):
            raise ValidationError(error_dict)


# TODO: Create two match entities per participation, it's more efficient.
class Participation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, editable=False)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, editable=False)
    # FIXME: Link to User? Otherwise, a cross-season match is technically possible.
    giftee = models.OneToOneField(
        "self",
        related_name="santa",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        editable=False,
        verbose_name="получатель подарка",
    )

    fullname = models.CharField("полное имя", max_length=80)
    postcode = models.CharField("индекс", max_length=20)
    address = models.TextField("адрес", max_length=200)
    country = CountryField("страна", null=True)

    gift_shipped_at = models.DateTimeField("подарок отправлен", blank=True, null=True, db_column="gift_sent")
    gift_delivered_at = models.DateTimeField("подарок получен", blank=True, null=True, db_column="gift_received")

    class Meta:
        unique_together = ["season", "user"]
        permissions = [
            ("view_participation_address", "Может видеть почтовый адрес участника"),
        ]

    def __str__(self):
        return "{} @ {}".format(self.user, self.season)


class Message(models.Model):
    # TODO: (from, to, season)? Otherwise, cross-season messages are technically possible
    sender = models.ForeignKey(Participation, on_delete=models.CASCADE, related_name="+")
    recipient = models.ForeignKey(Participation, on_delete=models.CASCADE, related_name="+")
    text = models.TextField(max_length=400, db_column="body")
    send_date = models.DateTimeField(default=timezone.now, db_index=True, editable=False)
    read_date = models.DateTimeField(blank=True, null=True, db_index=True, editable=False)

    class Meta:
        ordering = ["send_date"]


class BanRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ban_history", editable=False)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+", editable=False)
    reason = models.CharField("причина", max_length=200)
    is_banned = models.BooleanField("забанен", default=False, editable=False)
    date = models.DateTimeField(default=timezone.now, editable=False)


class Event(models.Model):
    LOGGED_IN = 1
    LOGGED_OUT = 2
    ENROLLED = 3
    UNENROLLED = 4
    GIFT_SENT = 5
    GIFT_RECEIVED = 6
    SANTA_MAILED = 7
    GIFTEE_MAILED = 8
    BANNED = 9
    UNBANNED = 10
    NOTE_UPDATED = 11
    SHIPMENT_CANCELED = 12
    SEASON_CREATED = 13
    UNSUBSCRIBED = 14
    TYPES = [
        (LOGGED_IN, "Вход в систему"),
        (LOGGED_OUT, "Выход из системы"),
        (ENROLLED, "Запись на участие"),
        (UNENROLLED, "Отказ от участия"),
        (GIFT_SENT, "Отправка подарка"),
        (GIFT_RECEIVED, "Получение подарка"),
        (SANTA_MAILED, "Письмо Деду Морозу"),
        (GIFTEE_MAILED, "Письмо получателю"),
        (BANNED, "Блокировка пользователя"),
        (UNBANNED, "Разблокировка пользователя"),
        (NOTE_UPDATED, "Заметка обновлена"),
        (SHIPMENT_CANCELED, "Отмена отправки"),
        (SEASON_CREATED, "Новый сезон"),
        (UNSUBSCRIBED, "Отписка от EMail"),
    ]

    typ = models.IntegerField("событие", choices=TYPES)
    sub = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="действующее лицо", related_name="events")
    obo = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="+")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name="пользователь", related_name="+")
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, verbose_name="сезон", related_name="events")
    time = models.DateTimeField("дата и время", default=timezone.now)
    ip_address = models.GenericIPAddressField("IP-адрес", null=True)

    class Meta:
        verbose_name = "событие"
        verbose_name_plural = "события"
