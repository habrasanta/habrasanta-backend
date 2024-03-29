import datetime
import html
import json
import requests

from django_countries import countries
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, F, Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views import View
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, PermissionDenied, NotFound
from rest_framework.permissions import BasePermission, IsAuthenticated, IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from urllib.parse import urlparse

from habrasanta.celery import send_email, send_notification, give_badge
from habrasanta.serializers import (
    AsyncResultSerializer,
    BanRecordSerializer,
    EventSerializer,
    MessageBulkSerializer,
    MessageSerializer,
    ParticipationSerializer,
    SeasonSerializer,
    TestEMailSerializer,
    TestNotificationSerializer,
    UserInfoSerializer,
    UserSerializer,
    MarkShippedSerializer,
    MarkDeliveredSerializer,
)
from habrasanta.utils import fetch_habr_profile
from habrasanta.models import Event, Message, Participation, Season, User


class GenericAPIError(APIException):
    """
    Override APIException to avoid status code 5xx.
    """
    status_code = status.HTTP_418_IM_A_TEAPOT


class SeasonViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SeasonSerializer
    queryset = Season.objects.all()

    def get_permissions(self):
        if self.action == "create":
            return [IsAdminUser()]
        return super().get_permissions()

    def create(self, request):
        """
        Creates a new season.

        The user calling this method must be an admin.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        season = serializer.save()
        Event.objects.create(
            typ=Event.SEASON_CREATED,
            sub=request.user,
            season=season,
        )
        return Response(serializer.data)

    @action(detail=False)
    @method_decorator(cache_control(public=True))
    def latest(self, request):
        """
        Returns the latest season or 404 if there are no seasons yet.
        """
        try:
            season = Season.objects.latest()
        except Season.DoesNotExist:
            raise NotFound()
        serializer = self.get_serializer(season)
        return Response(serializer.data)

    @action(
        detail=True,
        serializer_class=ParticipationSerializer,
        permission_classes=[IsAuthenticated],
    )
    @method_decorator(cache_control(private=True))
    def participation(self, request, pk):
        """
        Returns the participation of the current user in the given season
        or an error, if the user is not participating.
        """
        season = self.get_object()
        participation = self.get_participation(season)
        serializer = self.get_serializer(participation)
        return Response(serializer.data)

    @participation.mapping.post
    def create_participation(self, request, pk):
        """
        Enrolls the current user to the given season.

        An error occurs if:
        - The registration to this season has closed.
        - The user is not qualified for participation in our club (does the user have enough karma?)
        - The user is already enrolled for this season (is another tab open?)
        """
        season = self.get_object()
        self.check_season_active(season)
        if not season.is_registration_open:
            raise GenericAPIError("Регистрация на этот сезон уже невозможна", "the_die_is_cast")
        if not request.user.can_participate:
            raise PermissionDenied("Вы не можете участвовать в нашем клубе", "unqualified")
        if Participation.objects.filter(user=self.request.user, season=season).exists():
            raise GenericAPIError("Вы уже зарегистрированы на этот сезон", "dual_participation")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(season=season, user=request.user)
        season.member_count += 1
        season.save()
        Event.objects.create(
            typ=Event.ENROLLED,
            sub=request.user,
            season=season,
            ip_address=request.META["REMOTE_ADDR"],
        )
        return Response({
            "season": SeasonSerializer(season).data,
            "participation": serializer.validated_data,
        })

    @participation.mapping.delete
    def cancel_participation(self, request, pk):
        """
        Cancels the participation of the current user in the given season.

        An error occurs if:
        - The user is not participating in this season.
        - The registration has closed (too late - now, you must send a gift).
        """
        season = self.get_object()
        self.check_season_active(season)
        participation = self.get_participation(season)
        if not season.is_registration_open:
            raise GenericAPIError("Нельзя отказаться после окончания регистрации", "the_die_is_cast")
        participation.delete()
        season.member_count -= 1
        season.save()
        Event.objects.create(
            typ=Event.UNENROLLED,
            sub=request.user,
            season=season,
            ip_address=request.META["REMOTE_ADDR"],
        )
        return Response({
            "season": SeasonSerializer(season).data,
            "participation": None,
        })

    @action(
        detail=True,
        methods=["DELETE"],
        permission_classes=[IsAdminUser],
        url_path="participants/(?P<login>[^/.]+)",
    )
    def kick_participant(self, request, pk, login):
        """
        Cancels participation of the given user.

        Use with caution! It's one of the most dangerous API methods :-)
        Doing a backup before calling this method is highly recommended.

        The user calling this method must be an admin.
        """
        season = self.get_object()
        user = get_object_or_404(User, login__iexact=login)
        participation = get_object_or_404(Participation, user=user, season=season)
        if season.is_registration_open:
            # Easy peasy :-)
            participation.delete()
        else:
            # Reconnect participants.
            santa = participation.santa
            giftee = participation.giftee
            assert santa
            assert giftee
            participation.delete()
            participation = None
            santa.giftee = giftee
            santa.save()
            # Avoid loops of less than 3 people.
            assert giftee.giftee != santa
            # Send notifications.
            transaction.on_commit(send_notification.s(
                santa.user.id,
                "Замена получателя подарка! Посмотреть адрес нового получателя можно в " +
                "<a href=\"https://habra-adm.ru/{}/profile/\">профиле</a>.".format(season.id)
            ).delay)
            transaction.on_commit(send_email.s(
                santa.user.id,
                "замена получателя подарка",
                "Приветствуем!\n\n" +
                "Так получилось, что ваш Анонимный Получатель Подарка был заменён. " +
                "Для выяснения подробностей свяжитесь с пользователем @clubadm на Хабре - возможно, ещё не всё потеряно!"
            ).delay)
            transaction.on_commit(send_notification.s(
                giftee.user.id,
                "Замена Анонимного Деда Мороза!"
            ).delay)
            transaction.on_commit(send_email.s(
                giftee.user.id,
                "замена Деда Мороза",
                "Приветствуем!\n\n" +
                "Так получилось, что ваш Анонимный Дед Мороз был заменен (на не менее анонимного). " +
                "Для выяснения причин свяжитесь с пользователем @clubadm на Хабре - возможно, ещё не всё потеряно!"
            ).delay)
            # TODO: what about private messages in the chat?
        # Send a notification to the user itself.
        transaction.on_commit(send_notification.s(
            user.id,
            "Кто-то из организаторов отменил ваше участие в АДМ-{}.".format(season.id)
        ).delay)
        transaction.on_commit(send_email.s(
            user.id,
            "ваше участие отменено",
            "Приветствуем!\n\n" +
            "Ваше участие в АДМ-{} было отменено. ".format(season.id) +
            "Для выяснения подробностей свяжитесь с пользователем @clubadm на Хабре - возможно, ещё не всё потеряно!"
        ).delay)
        # Update counters.
        season.member_count -= 1
        season.save()
        # Log the event.
        Event.objects.create(
            typ=Event.UNENROLLED,
            sub=request.user,
            user=user,
            season=season,
            ip_address=request.META["REMOTE_ADDR"],
        )
        # Send 204 No Content.
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def mark_shipped(self, request, pk):
        """
        Tells the club, the current user has shipped a gift to their giftee.

        The giftee will be automatically notified.

        An error occurs if:
        - The user is not participating in this season.
        - The user has no giftee assigned yet (is registration still open?)
        - The user has already told the club, they had sent a gift.
        """
        season = self.get_object()
        self.check_season_active(season)
        participation = self.get_participation(season)
        if not participation.giftee:
            raise NotFound("Вам еще не назначен получателя подарка")
        if participation.gift_shipped_at:
            raise GenericAPIError("Вами уже был отправлен один подарок", "already_shipped")
        season.shipped_count += 1
        season.save()
        participation.gift_shipped_at = timezone.now()
        participation.save()
        Event.objects.create(
            typ=Event.GIFT_SENT,
            sub=request.user,
            season=season,
            ip_address=request.META["REMOTE_ADDR"],
        )
        transaction.on_commit(send_notification.s(
            participation.giftee.user.id,
            "Анонимный Дед Мороз отправил подарок! Когда получите, не забудьте отметить это в " +
            "<a href=\"https://habra-adm.ru/{}/profile/\">профиле</a>.".format(season.id)
        ).delay)
        transaction.on_commit(send_email.s(
            participation.giftee.user.id,
            "Вам отправили подарок!",
            "Привет, внук!\n\n" +
            "Похоже, ты хорошо вёл себя в этом году - Анонимный Дед Мороз отправил тебе подарок!\n\n" +
            "Пожалуйста, не забудь отметить в профиле " +
            "(https://habra-adm.ru/{}/profile/), ".format(season.id) +
            "когда получишь подарок.\n\n" +
            "Всего наилучшего в новом году!"
        ).delay)
        return Response({
            "season": self.get_serializer(season).data,
            "participation": ParticipationSerializer(participation).data,
        })

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def mark_delivered(self, request, pk):
        """
        Tells the club the current user has received a gift.

        The santa will be automatically notified.

        An error occurs if:
        - The user is not participating in this season.
        - The user has no santa assigned yet.
        - The user has already told the club, they had received a gift.
        - Santa hasn't told the club yet, the gift was sent.
        """
        season = self.get_object()
        self.check_season_active(season)
        participation = self.get_participation(season)
        if not hasattr(participation, "santa"):
            raise NotFound("Вам еще не назначен Дед Мороз")
        if participation.gift_delivered_at:
            raise GenericAPIError("Вами уже был получен один подарок", "already_delivered")
        if not participation.santa.gift_shipped_at:
            raise GenericAPIError("Нельзя получить подарок до того, как он был отправлен", "not_shipped")
        season.delivered_count += 1
        season.save()
        participation.gift_delivered_at = timezone.now()
        participation.save()
        Event.objects.create(
            typ=Event.GIFT_RECEIVED,
            sub=request.user,
            season=season,
            ip_address=request.META["REMOTE_ADDR"],
        )
        transaction.on_commit(send_notification.s(
            participation.santa.user.id,
            "Ваш АПП отметил в профиле, что подарок получен!"
        ).delay)
        transaction.on_commit(send_email.s(
            participation.santa.user.id,
            "ваш получатель отметил, что получил подарок!",
            "Привет, Анонимный Дед Мороз!\n\n" +
            "Новогоднее чудо случилось — ваш Анонимный Получатель Подарка отметил, что получил подарок!\n\n" +
            "Поздравляем и желаем всего наилучшего в новом году!"
        ).delay)
        # Use the task queue, because Habr is down sometimes and the badge is important for some users.
        transaction.on_commit(give_badge.s(participation.santa.user.id).delay)
        return Response({
            "season": self.get_serializer(season).data,
            "participation": ParticipationSerializer(participation).data,
        })

    @action(
        detail=True,
        serializer_class=MessageSerializer,
        permission_classes=[IsAuthenticated],
    )
    @method_decorator(cache_control(private=True))
    def giftee_chat(self, request, pk):
        """
        Returns all chat messages between the current user and their giftee in the given season.

        An error occurs if:
        - The user is not participating in this season.
        - The user has no giftee assigned yet (is registration still open?)
        """
        season = self.get_object()
        participation = self.get_participation(season)
        if not participation.giftee:
            raise NotFound("Вам еще не назначен получателя подарка")
        # TODO: select_related() ? Check the SQL queries!
        messages = Message.objects.filter(
            Q(sender=participation, recipient=participation.giftee) |
            Q(sender=participation.giftee, recipient=participation)
        )
        serializer = self.get_serializer(messages, many=True, context={ "me": participation })
        return Response(serializer.data)

    @giftee_chat.mapping.post
    def post_giftee_chat(self, request, pk):
        """
        Sends a chat message to the giftee of the current user in the given season.

        An error occurs if:
        - The user is not participating in this season.
        - The user has no giftee assigned yet (is registration still open?)
        """
        season = self.get_object()
        self.check_season_active(season)
        participation = self.get_participation(season)
        if not participation.giftee:
            raise NotFound("Вам еще не назначен получателя подарка")
        # TODO: prevent spamming with too many messages
        serializer = self.get_serializer(data=request.data, context={ "me": participation })
        serializer.is_valid(raise_exception=True)
        serializer.save(sender=participation, recipient=participation.giftee)
        Event.objects.create(
            typ=Event.GIFTEE_MAILED,
            sub=request.user,
            season=season,
            ip_address=request.META["REMOTE_ADDR"],
        )
        # Notification will be send by cron.
        return Response(serializer.data)

    @action(
        detail=True,
        serializer_class=MessageSerializer,
        permission_classes=[IsAuthenticated],
    )
    @method_decorator(cache_control(private=True))
    def santa_chat(self, request, pk):
        """
        Returns all chat messages between the current user and their santa in the given season.

        An error occurs if:
        - The user is not participating in this season.
        - The user has no santa assigned yet (is registration still open?)
        """
        season = self.get_object()
        participation = self.get_participation(season)
        if not hasattr(participation, "santa"):
            raise NotFound("Вам еще не назначен Дед Мороз")
        # TODO: select_related() ? Check the SQL queries!
        messages = Message.objects.filter(
            Q(sender=participation, recipient=participation.santa) |
            Q(sender=participation.santa, recipient=participation)
        )
        serializer = self.get_serializer(messages, many=True, context={ "me": participation })
        return Response(serializer.data)

    @santa_chat.mapping.post
    def post_santa_chat(self, request, pk):
        """
        Sends a chat message to the santa of the current user in the given season.

        An error occurs if:
        - The user is not participating in this season.
        - The user has no santa assigned yet (is registration still open?)
        """
        season = self.get_object()
        self.check_season_active(season)
        participation = self.get_participation(season)
        if not hasattr(participation, "santa"):
            raise NotFound("Вам еще не назначен Дед Мороз")
        # TODO: prevent spamming with too many messages
        serializer = self.get_serializer(data=request.data, context={ "me": participation })
        serializer.is_valid(raise_exception=True)
        serializer.save(sender=participation, recipient=participation.santa)
        Event.objects.create(
            typ=Event.SANTA_MAILED,
            sub=request.user,
            season=season,
            ip_address=request.META["REMOTE_ADDR"],
        )
        # Notification will be send by cron.
        return Response(serializer.data)

    @action(
        detail=True,
        serializer_class=EventSerializer,
        permission_classes=[IsAdminUser],
    )
    @method_decorator(cache_control(private=True))
    def events(self, request, pk):
        """
        Returns all events associated with this season,
        e.g. enrollments, sending or receiving gifts, etc.

        The user calling this method must be an admin.
        """
        season = self.get_object()
        serializer = self.get_serializer(season.events, many=True)
        return Response(serializer.data)

    @action(detail=True)
    @method_decorator(cache_control(public=True))
    def countries(self, request, pk):
        """
        Shows country statistics for the given season.
        """
        season = self.get_object()
        stats = Participation.objects.filter(
            season=season,
        ).values("country").annotate(
            count=Count("id"),
        ).order_by("-count", "country")
        result = {}
        for item in stats:
            result[item["country"]] = item["count"]
        return Response(result)

    def check_season_active(self, season):
        if season.is_closed:
            raise GenericAPIError("Этот сезон находится в архиве", "season_archived")

    def get_participation(self, season):
        try:
            return Participation.objects.select_related("santa", "giftee").get(user=self.request.user, season=season)
        except Participation.DoesNotExist:
            raise GenericAPIError("Ой, а вы во всем этом и не участвуете", "not_participating")


class MessageViewSet(viewsets.GenericViewSet):
    permission_classes=[IsAuthenticated]
    serializer_class = MessageSerializer
    queryset = Season.objects.all()

    @action(
        detail=False,
        methods=["post"],
        serializer_class=MessageBulkSerializer,
    )
    def mark_read(self, request):
        """
        Marks the messages with the given IDs as read and returns the number of updated messages.

        On success, this number is equal to the number of given IDs.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["ids"]
        count = Message.objects.filter(
            id__in=ids,
            recipient__user=request.user,
            read_date__isnull=True,
            # read_date was introduced on this day, all messages before must stay NULL.
            send_date__gte=timezone.make_aware(datetime.datetime(2016, 12, 20))
        ).update(read_date=timezone.now())
        return Response({ "updated": count })


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes=[IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "login__iexact"
    lookup_url_kwarg = "login"

    @action(
        detail=True,
        methods=["post"],
        serializer_class=TestNotificationSerializer,
    )
    def send_notification(self, request, login):
        """
        Sends a notification on Habr for this user, mostly for testing purposes.

        The user calling this method must be an admin.
        """
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        async_result = send_notification.delay(user.id, serializer.validated_data["text"])
        return Response(AsyncResultSerializer(async_result).data, status=status.HTTP_202_ACCEPTED)

    @action(
        detail=True,
        methods=["post"],
        serializer_class=TestEMailSerializer,
    )
    def send_email(self, request, login):
        """
        Sends an email to this user, mostly for testing purposes.

        The user calling this method must be an admin.
        """
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        async_result = send_email.delay(
            user.id,
            serializer.validated_data["subject"],
            serializer.validated_data["body"]
        )
        return Response(AsyncResultSerializer(async_result).data, status=status.HTTP_202_ACCEPTED)

    @action(
        detail=True,
        serializer_class=EventSerializer,
        permission_classes=[IsAdminUser],
    )
    @method_decorator(cache_control(private=True))
    def events(self, request, login):
        """
        Returns all events caused by this user.

        The user calling this method must be an admin.
        """
        user = self.get_object()
        serializer = self.get_serializer(user.events, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        serializer_class=BanRecordSerializer,
    )
    def ban_history(self, request, login):
        """
        Shows the ban history.

        The user calling this method must be an admin.
        """
        user = self.get_object()
        serializer = self.get_serializer(user.ban_history, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        serializer_class=BanRecordSerializer,
    )
    def ban(self, request, login):
        """
        Bans the given user. The reason is not visible to the user, yet must always be provided.

        An error occurs if:
        - The user is already banned.
        - The user is trying to ban themself (it is, however, possible to unban yourself).

        The user calling this method must be an admin.
        """
        user = self.get_object()
        if user.is_banned:
            raise GenericAPIError("Пользователь '{}' уже в бане".format(user.login))
        if user == request.user:
            raise GenericAPIError("Не стоит банить самого себя (потеряете доступ в админку!)")
        user.is_banned = True
        user.save()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user, admin=request.user, is_banned=True)
        Event.objects.create(
            typ=Event.BANNED,
            sub=request.user,
            user=user,
            ip_address=request.META["REMOTE_ADDR"],
        )
        transaction.on_commit(send_notification.s(
            user.id,
            "Ваш аккаунт заблокирован. Для выяснения причин свяжитесь с пользователем @clubadm."
        ).delay)
        transaction.on_commit(send_email.s(
            user.id,
            "Ваш аккаунт заблокирован",
            "Приветствуем! Ваш аккаунт в Клубе Анонимных Дедов Морозов был заблокирован.\n\n" +
            "Для выяснения причин свяжитесь с пользователем @clubadm на Хабре - возможно, ещё не всё потеряно!"
        ).delay)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        serializer_class=BanRecordSerializer,
    )
    def unban(self, request, login):
        """
        Unbans the given user. The reason is not visible to the user, yet must always be provided.

        The user calling this method must be an admin.
        """
        user = self.get_object()
        if not user.is_banned:
            raise GenericAPIError("Пользователь '{}' уже разбанен".format(user.login))
        user.is_banned = False
        user.save()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user, admin=request.user, is_banned=False)
        Event.objects.create(
            typ=Event.UNBANNED,
            sub=request.user,
            user=user,
            ip_address=request.META["REMOTE_ADDR"],
        )
        transaction.on_commit(send_notification.s(
            user.id,
            "Ваш аккаунт разблокирован. Желаем вам счастливого Нового Года и Рождества! :-)"
        ).delay)
        transaction.on_commit(send_email.s(
            user.id,
            "Ваш аккаунт разблокирован",
            "Приветствуем!\n\n" +
            "Ваш аккаунт в Клубе Анонимных Дедов Морозов был разблокирован.\n\n" +
            "Поздравляем и желаем всего наилучшего в новом году!"
        ).delay)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def allow_emails(self, request, login):
        """
        Allows sending emails to this user.

        Sometimes users click the unsubscribe link incidentally and ask us to resubscribe them again,
        this method does exactly that.

        The user calling this method must be an admin.
        """
        user = self.get_object()
        if user.email_allowed:
            raise GenericAPIError("Пользователь '{}' уже подписан на email-уведомления".format(user.login))
        user.email_allowed = True
        user.save()
        Event.objects.create(
            typ=Event.SUBSCRIBED,
            sub=request.user,
            user=user,
            ip_address=request.META["REMOTE_ADDR"],
        )
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        serializer_class=MarkShippedSerializer,
        url_path="seasons/(?P<season_id>\\d+)/mark_shipped",
    )
    def mark_shipped(self, request, login, season_id):
        """
        Marks the gift as shipped in the given season.

        The user calling this method must be an admin.
        """
        user = self.get_object()
        try:
            participation = Participation.objects.get(user=user, season_id=season_id)
        except Participation.DoesNotExist:
            raise GenericAPIError("Этот пользователь не участвует в этом сезоне", "not_participating")
        if not participation.giftee:
            raise NotFound("Этому пользователю еще не назначен получателя подарка")
        if participation.gift_shipped_at:
            raise GenericAPIError("Этот пользователь уже отправил подарок", "already_shipped")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participation.season.shipped_count += 1
        participation.season.save()
        participation.gift_shipped_at = serializer.validated_data["gift_shipped_at"]
        participation.save()
        Event.objects.create(
            typ=Event.GIFT_SENT,
            sub=request.user,
            season=participation.season,
            obo=user,
            ip_address=request.META["REMOTE_ADDR"],
        )
        # Notifications for the user themselves:
        transaction.on_commit(send_notification.s(
            user.id,
            "Лучше поздно, чем никогда - спасибо, что отправили подарок!"
        ).delay)
        transaction.on_commit(send_email.s(
            user.id,
            "запоздавшее новогоднее волшебство",
            "Лучше поздно, чем никогда - спасибо, что отправили подарок!"
        ).delay)
        # Notifications for their giftee:
        transaction.on_commit(send_notification.s(
            participation.giftee.user.id,
            "Лучше поздно, чем никогда: администраторы сервиса получили подтверждение отправки вам подарка, ожидайте!"
        ).delay)
        transaction.on_commit(send_email.s(
            participation.giftee.user.id,
            "запоздавшее новогоднее волшебство",
            "Лучше поздно, чем никогда: администраторы сервиса получили подтверждение отправки вам подарка, ожидайте!"
        ).delay)
        return Response({
            "season": SeasonSerializer(participation.season).data,
            "participation": ParticipationSerializer(participation).data,
        })

    @action(
        detail=True,
        methods=["post"],
        serializer_class=MarkDeliveredSerializer,
        url_path="seasons/(?P<season_id>\\d+)/mark_delivered",
    )
    def mark_delivered(self, request, login, season_id):
        """
        Marks the gift as delivered in the given season.

        The user calling this method must be an admin.
        """
        user = self.get_object()
        try:
            participation = Participation.objects.get(user=user, season_id=season_id)
        except Participation.DoesNotExist:
            raise GenericAPIError("Этот пользователь не участвует в этом сезоне", "not_participating")
        if not hasattr(participation, "santa"):
            raise NotFound("Этому пользователю еще не назначен Дед Мороз, красный нос")
        if participation.gift_delivered_at:
            raise GenericAPIError("Этим пользователем уже был получен подарок", "already_delivered")
        if not participation.santa.gift_shipped_at:
            raise GenericAPIError("Нельзя получить подарок до того, как он был отправлен", "not_shipped")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participation.season.delivered_count += 1
        participation.season.save()
        participation.gift_delivered_at = serializer.validated_data["gift_delivered_at"]
        participation.save()
        Event.objects.create(
            typ=Event.GIFT_RECEIVED,
            sub=request.user,
            season=participation.season,
            obo=user,
            ip_address=request.META["REMOTE_ADDR"],
        )
        # Use the task queue, because Habr is down sometimes and the badge is important for some users.
        transaction.on_commit(give_badge.s(participation.santa.user.id).delay)
        # Notifications for the user themselves:
        transaction.on_commit(send_notification.s(
            user.id,
            "Вы забыли отметить получение подарка, поэтому администраторы сервиса сделали это за вас."
        ).delay)
        transaction.on_commit(send_email.s(
            user.id,
            "запоздавшее новогоднее волшебство",
            "Приветствуем!\n\n" +
            "Вы забыли отметить получение подарка, поэтому администраторы сервиса сделали это за вас."
        ).delay)
        # Notifications for their santa:
        transaction.on_commit(send_notification.s(
            participation.santa.user.id,
            "Ваш получатель подарка куда-то пропал или забыл отметить, что получил подарок. Поэтому подтверждаем получение подарка за него. Спасибо за участие!"
        ).delay)
        transaction.on_commit(send_email.s(
            participation.santa.user.id,
            "запоздавшее новогоднее волшебство",
            "Привет, Анонимный Дед Мороз!\n\n" +
            "Ваш получатель подарка куда-то пропал или забыл отметить, что получил подарок. Поэтому подтверждаем получение подарка за него.\n\n" +
            "Спасибо за участие!"
        ).delay)
        return Response({
            "season": SeasonSerializer(participation.season).data,
            "participation": ParticipationSerializer(participation).data,
        })


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes=[IsAdminUser]
    serializer_class = EventSerializer
    queryset = Event.objects.all()


class CountryViewSet(viewsets.ViewSet):
    @method_decorator(cache_control(public=True, max_age=60 * 60 * 24 * 30))
    def list(self, request):
        """
        Lists all accepted countries.
        """
        return Response(sorted([{
            "code": code,
            "name": name,
        } for code, name in countries], key=lambda c: c["name"]))


class InfoView(APIView):
    def get(self, request, format=None):
        data = {
            "csrf_token": get_token(request),
            "is_authenticated": request.user.is_authenticated,
            "is_active": False,
            "can_participate": False,
            "is_debug": settings.DEBUG,
        }
        if request.user.is_authenticated:
            try:
                data["username"] = request.user.login
                data["avatar_url"] = request.user.avatar_url
                data["karma"] = request.user.karma
                data["is_readonly"] = request.user.is_readonly
                data["has_badge"] = request.user.has_badge
                data["is_active"] = not request.user.is_banned
                data["can_participate"] = request.user.can_participate
            except requests.exceptions.Timeout as e:
                return Response({ "error": str(e) }, status=504)
        return Response(data)


class LoginView(View):
    def get(self, request):
        next = request.GET.get("next")
        if not url_has_allowed_host_and_scheme(next, None):
            next = "/"
        if request.user.is_authenticated:
            return HttpResponseRedirect(next)
        redirect_uri = reverse("callback") + "?" + urlencode({ "next": next }) # TODO: move to state
        if settings.DEBUG:
            authorize_url = reverse("fake_authorize")
        else:
            authorize_url = settings.HABR_LOGIN_URL
        login_url = authorize_url + "?" + urlencode({
            "client_id": settings.HABR_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": request.build_absolute_uri(redirect_uri),
            "state": get_token(request),
        })
        return HttpResponseRedirect(login_url)


class CallbackView(View):
    def get(self, request):
        # TODO: check state
        next = request.GET.get("next")
        if not url_has_allowed_host_and_scheme(next, None):
            next = "/"
        if request.user.is_authenticated:
            # A lot of our users try to press the Back button immediately after login.
            return HttpResponseRedirect(next)
        code = request.GET.get("code")
        if not code:
            return render(request, "habrasanta/auth_error.html", status=500)
        user = authenticate(request, authorization_code=code)
        if not user:
            return render(request, "habrasanta/auth_error.html", status=500)
        login(request, user)
        return HttpResponseRedirect(next)


class LogoutView(View):
    def get(self, request):
        # TODO: check CSRF token
        logout(request)
        next = request.GET.get("next")
        if not url_has_allowed_host_and_scheme(next, None):
            next = "/"
        return HttpResponseRedirect(next)


class FakeAuthorizeView(View):
    def get(self, request):
        return render(request, "habrasanta/fake_authorize.html", {
            "redirect_uri": request.GET.get("redirect_uri"),
            "state": request.GET.get("state"),
        })

    def post(self, request):
        url = urlparse(request.POST.get("redirect_uri"))
        return HttpResponseRedirect(url.path + "?" + urlencode({
            "code": request.POST.get("username"),
            "state": request.POST.get("state"),
        }) + "&" + url.query)


@csrf_exempt # already validated by email_token
def unsubscribe(request):
    if not "uid" in request.GET:
        return render(request, "habrasanta/unsubscribed.html", {
            "error": "отсутствует ID пользователя",
        })
    try:
        user = User.objects.get(habr_id=request.GET.get("uid"))
    except User.DoesNotExist:
        return render(request, "habrasanta/unsubscribed.html", {
            "error": "пользователь с таким ID не найден",
        })
    if user.email_token != request.GET.get("token"):
        return render(request, "habrasanta/unsubscribed.html", {
            "error": "токен невалиден для этого пользователя",
        })
    if not user.email_allowed:
        return render(request, "habrasanta/unsubscribed.html", {
            "error": "у нас уже отмечено, что вы не хотите получать наши письма",
        })
    if request.method == "POST":
        Event.objects.create(
            typ=Event.UNSUBSCRIBED,
            sub=user,
            ip_address=request.META["REMOTE_ADDR"],
        )
        user.email_allowed = False
        user.save()
        return render(request, "habrasanta/unsubscribed.html", {
            "email": user.email,
        })
    return render(request, "habrasanta/unsubscribe.html", {
        "email": user.email,
        "uid": user.habr_id,
        "token": user.email_token,
    })


class HealthView(View):
    def get(self, request):
        return HttpResponse("okay", content_type="text/plain")
