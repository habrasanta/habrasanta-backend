from django_countries.serializers import CountryFieldMixin
from rest_framework import serializers

from habrasanta.models import BanRecord, Event, Message, Participation, Season, User


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = [
            "id",
            "registration_open",
            "registration_close",
            "season_close",
            "member_count",
            "shipped_count",
            "delivered_count",
            "is_registration_open",
            "is_closed",
            "is_matched",
            "gallery_url",
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "login", "is_staff", "is_active", "can_participate", "email_allowed", "last_online"]
        extra_kwargs = {
            "url": { "lookup_field": "login" },
        }


class MessageSerializer(serializers.ModelSerializer):
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "text", "send_date", "read_date", "is_author"]

    def get_is_author(self, message) -> bool:
        return message.sender_id == self.context["me"].id


class SantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participation
        fields = ["gift_shipped_at"]
        read_only_fields = fields


class GifteeSerializer(CountryFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = Participation
        fields = ["fullname", "postcode", "address", "country", "gift_delivered_at"]
        read_only_fields = fields


class ParticipationSerializer(CountryFieldMixin, serializers.ModelSerializer):
    santa = SantaSerializer(read_only=True)
    giftee = GifteeSerializer(read_only=True)

    class Meta:
        model = Participation
        fields = ["fullname", "postcode", "address", "country", "gift_shipped_at", "gift_delivered_at", "giftee", "santa"]
        read_only_fields = ["gift_shipped_at", "gift_delivered_at"]
        extra_kwargs = {
            # Required for all new participants now.
            "country": {"required": True},
        }


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "avatar_url", "is_stuff"]


class MessageBulkSerializer(serializers.Serializer):
    ids = serializers.ListField(child = serializers.IntegerField(min_value=0))


class TestNotificationSerializer(serializers.Serializer):
    text = serializers.CharField()


class TestEMailSerializer(serializers.Serializer):
    subject = serializers.CharField()
    body = serializers.CharField()


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["time", "typ", "sub", "obo", "user", "season", "ip_address"]
        read_only_fields = fields


class AsyncResultSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    date_done = serializers.DateTimeField(read_only=True)
    state = serializers.CharField(read_only=True)


class BanRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BanRecord
        fields = ["admin", "reason", "is_banned", "date"]
