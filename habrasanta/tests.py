import json

from datetime import timedelta
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from habrasanta.models import Message, Participation, Season, User


class UserTestCase(TestCase):
    def test_profile(self):
        u = User()
        u._profile = {
            "karma": 42,
            "has_badge": False,
            "is_readonly": False,
            "avatar_url": None,
        }
        self.assertEqual(u.karma, 42)
        self.assertFalse(u.has_badge)
        self.assertFalse(u.is_readonly)
        self.assertEqual(u.avatar_url, "https://hsto.org/storage/habrastock/i/avatars/stub-user-middle.gif")
        u._profile = {
            "karma": 0,
            "has_badge": True,
            "is_readonly": True,
            "avatar_url": "//habrastorage.org/getpro/habr/avatars/7bf/80e/da6/7bf80eda638211ca4a38ed48b4058c2d.png",
        }
        self.assertEqual(u.karma, 0)
        self.assertTrue(u.has_badge)
        self.assertTrue(u.is_readonly)
        self.assertEqual(u.avatar_url, "//habrastorage.org/getpro/habr/avatars/7bf/80e/da6/7bf80eda638211ca4a38ed48b4058c2d.png")

    def test_django_getters(self):
        u = User(login="kafeman")
        self.assertTrue(u.is_active)
        self.assertTrue(u.is_staff)
        self.assertFalse(u.is_anonymous)
        self.assertTrue(u.is_authenticated)
        self.assertEqual(u.get_username(), "kafeman")

    def test_can_participate(self):
        u = User()
        u._profile = { "karma": 0, "has_badge": False, "is_readonly": False }
        self.assertFalse(u.can_participate)
        u._profile = { "karma": 0, "has_badge": True, "is_readonly": False }
        self.assertTrue(u.can_participate)
        u._profile = { "karma": 100, "has_badge": False, "is_readonly": False }
        self.assertTrue(u.can_participate)
        u._profile = { "karma": 100, "has_badge": True, "is_readonly": True }
        self.assertFalse(u.can_participate)
        u._profile = { "karma": 100, "has_badge": True, "is_readonly": False }
        u.is_banned = True
        self.assertFalse(u.can_participate)


class SeasonTestCase(TestCase):
    def test_str(self):
        s = Season(id=1970)
        self.assertEqual(str(s), "АДМ 1970")

    def test_is_registration_open(self):
        s = Season(registration_open=timezone.now() + timedelta(hours=1))
        self.assertFalse(s.is_registration_open)
        s.registration_open = timezone.now() - timedelta(hours=2)
        s.registration_close = timezone.now() - timedelta(hours=1)
        self.assertFalse(s.is_registration_open)
        s.registration_close = timezone.now() + timedelta(hours=1)
        self.assertTrue(s.is_registration_open)

    def test_is_closed(self):
        s = Season(season_close=timezone.now() + timedelta(hours=1))
        self.assertFalse(s.is_closed)
        s.season_close = timezone.now() - timedelta(hours=1)
        self.assertTrue(s.is_closed)

    def test_is_matched(self):
        s = Season()
        self.assertFalse(s.is_matched)
        s.address_match = timezone.now()
        self.assertTrue(s.is_matched)

class SeasonViewSetTestCase(TestCase):
    def test_list(self):
        client = APIClient()
        response = client.get("/api/v1/seasons")
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["count"], 0)
        self.assertEqual(len(obj["results"]), 0)
        Season.objects.create(
            id=2007,
            registration_open=timezone.now() - timedelta(hours=2),
            registration_close=timezone.now() - timedelta(hours=1),
            season_close=timezone.now() + timedelta(hours=1),
        )
        response = client.get("/api/v1/seasons")
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["count"], 1)
        self.assertEqual(len(obj["results"]), 1)
        self.assertEqual(obj["results"][0]["id"], 2007)
        self.assertEqual(obj["results"][0]["member_count"], 0)
        self.assertEqual(obj["results"][0]["shipped_count"], 0)
        self.assertEqual(obj["results"][0]["delivered_count"], 0)
        self.assertEqual(obj["results"][0]["is_registration_open"], False)
        self.assertEqual(obj["results"][0]["is_closed"], False)
        self.assertEqual(obj["results"][0]["is_matched"], False)
        self.assertEqual(obj["results"][0]["gallery_url"], "")

    def test_create(self):
        client = APIClient()
        response = client.post("/api/v1/seasons")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        client.force_authenticate(user=User(login="exploitable"))
        response = client.post("/api/v1/seasons")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "У вас недостаточно прав для выполнения данного действия."
        )
        user = User.objects.create(login="kafeman")
        client.force_authenticate(user=user)
        response = client.post("/api/v1/seasons")
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(obj["id"], ["Обязательное поле."])
        self.assertEqual(obj["registration_open"], ["Обязательное поле."])
        self.assertEqual(obj["registration_close"], ["Обязательное поле."])
        self.assertEqual(obj["season_close"], ["Обязательное поле."])
        response = client.post("/api/v1/seasons", {
            "id": 2007,
            "registration_open": "2007-11-01T00:00:00Z",
            "registration_close": "2007-11-01T00:00:00Z",
            "season_close": "2007-11-01T00:00:00Z",
        })
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["id"], 2007)
        self.assertEqual(obj["registration_open"], "2007-11-01T00:00:00Z")
        self.assertEqual(obj["registration_close"], "2007-11-01T00:00:00Z")
        self.assertEqual(obj["season_close"], "2007-11-01T00:00:00Z")
        self.assertEqual(obj["member_count"], 0)
        self.assertEqual(obj["shipped_count"], 0)
        self.assertEqual(obj["delivered_count"], 0)
        self.assertEqual(obj["is_registration_open"], False)
        self.assertEqual(obj["is_closed"], True)
        self.assertEqual(obj["is_matched"], False)
        self.assertEqual(obj["gallery_url"], "")

    def test_retrieve(self):
        client = APIClient()
        response = client.get("/api/v1/seasons/2007")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        Season.objects.create(
            id=2007,
            registration_open=timezone.now() - timedelta(hours=2),
            registration_close=timezone.now() - timedelta(hours=1),
            season_close=timezone.now() + timedelta(hours=1),
        )
        response = client.get("/api/v1/seasons/2007")
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["id"], 2007)
        self.assertEqual(obj["member_count"], 0)
        self.assertEqual(obj["shipped_count"], 0)
        self.assertEqual(obj["delivered_count"], 0)
        self.assertEqual(obj["is_registration_open"], False)
        self.assertEqual(obj["is_closed"], False)
        self.assertEqual(obj["is_matched"], False)
        self.assertEqual(obj["gallery_url"], "")

    def test_events(self):
        client = APIClient()
        response = client.get("/api/v1/seasons/2007/events")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        client.force_authenticate(user=User(login="exploitable"))
        response = client.get("/api/v1/seasons/2007/events")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "У вас недостаточно прав для выполнения данного действия."
        )
        # TODO: We're not really interested in this method now,
        # just make sure only admins may access it...

    def test_giftee_chat(self):
        client = APIClient()
        response = client.get("/api/v1/seasons/2007/giftee_chat")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.get("/api/v1/seasons/2007/giftee_chat")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        season = Season.objects.create(
            id=2007,
            registration_open=timezone.now() - timedelta(hours=2),
            registration_close=timezone.now() - timedelta(hours=1),
            season_close=timezone.now() + timedelta(hours=1),
        )
        response = client.get("/api/v1/seasons/2007/giftee_chat")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Ой, а вы во всем этом и не участвуете"
        )
        participation = Participation.objects.create(
            season=season,
            user=user,
        )
        response = client.get("/api/v1/seasons/2007/giftee_chat")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Вам еще не назначен получателя подарка"
        )
        another_user = User.objects.create(login="kafeman")
        giftee = Participation.objects.create(
            season=season,
            user=another_user,
        )
        participation.giftee = giftee
        participation.save()
        response = client.get("/api/v1/seasons/2007/giftee_chat")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"[]")
        Message.objects.create(
            sender=participation,
            recipient=giftee,
            text="Hello World",
        )
        Message.objects.create(
            sender=giftee,
            recipient=participation,
            text="Goodbye Cruel World",
        )
        response = client.get("/api/v1/seasons/2007/giftee_chat")
        self.assertEqual(response.status_code, 200)
        array = json.loads(response.content)
        self.assertEqual(len(array), 2)
        self.assertEqual(array[0]["text"], "Hello World")
        self.assertTrue(array[0]["is_author"])
        self.assertEqual(array[1]["text"], "Goodbye Cruel World")
        self.assertFalse(array[1]["is_author"])

    def test_post_giftee_chat(self):
        client = APIClient()
        response = client.post("/api/v1/seasons/2007/giftee_chat")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.post("/api/v1/seasons/2007/giftee_chat")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        season = Season.objects.create(
            id=2007,
            registration_open=timezone.now() - timedelta(hours=3),
            registration_close=timezone.now() - timedelta(hours=2),
            season_close=timezone.now() - timedelta(hours=1),
        )
        response = client.post("/api/v1/seasons/2007/giftee_chat")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Этот сезон находится в архиве"
        )
        Season.objects.filter(pk=2007).update(
            season_close=timezone.now() + timedelta(hours=1),
        )
        response = client.post("/api/v1/seasons/2007/giftee_chat")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Ой, а вы во всем этом и не участвуете"
        )
        participation = Participation.objects.create(
            season=season,
            user=user,
        )
        response = client.post("/api/v1/seasons/2007/giftee_chat")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Вам еще не назначен получателя подарка"
        )
        another_user = User.objects.create(login="kafeman")
        giftee = Participation.objects.create(
            season=season,
            user=another_user,
        )
        participation.giftee = giftee
        participation.save()
        response = client.post("/api/v1/seasons/2007/giftee_chat")
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(obj["text"], ["Обязательное поле."])
        response = client.post("/api/v1/seasons/2007/giftee_chat", {
            "text": "Hello World",
        })
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["text"], "Hello World")
        self.assertTrue(obj["is_author"])
        msg = Message.objects.get(sender=participation, recipient=giftee)
        self.assertEqual(msg.text, "Hello World")

    def test_santa_chat(self):
        client = APIClient()
        response = client.get("/api/v1/seasons/2007/santa_chat")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.get("/api/v1/seasons/2007/santa_chat")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        season = Season.objects.create(
            id=2007,
            registration_open=timezone.now() - timedelta(hours=2),
            registration_close=timezone.now() - timedelta(hours=1),
            season_close=timezone.now() + timedelta(hours=1),
        )
        response = client.get("/api/v1/seasons/2007/santa_chat")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Ой, а вы во всем этом и не участвуете"
        )
        participation = Participation.objects.create(
            season=season,
            user=user,
        )
        response = client.get("/api/v1/seasons/2007/santa_chat")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Вам еще не назначен Дед Мороз"
        )
        another_user = User.objects.create(login="kafeman")
        santa = Participation.objects.create(
            season=season,
            user=another_user,
            giftee=participation,
        )
        response = client.get("/api/v1/seasons/2007/santa_chat")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"[]")
        Message.objects.create(
            sender=participation,
            recipient=santa,
            text="Hello World",
        )
        Message.objects.create(
            sender=santa,
            recipient=participation,
            text="Goodbye Cruel World",
        )
        response = client.get("/api/v1/seasons/2007/santa_chat")
        self.assertEqual(response.status_code, 200)
        array = json.loads(response.content)
        self.assertEqual(len(array), 2)
        self.assertEqual(array[0]["text"], "Hello World")
        self.assertTrue(array[0]["is_author"])
        self.assertEqual(array[1]["text"], "Goodbye Cruel World")
        self.assertFalse(array[1]["is_author"])

    def test_post_santa_chat(self):
        client = APIClient()
        response = client.post("/api/v1/seasons/2007/santa_chat")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.post("/api/v1/seasons/2007/santa_chat")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        season = Season.objects.create(
            id=2007,
            registration_open=timezone.now() - timedelta(hours=3),
            registration_close=timezone.now() - timedelta(hours=2),
            season_close=timezone.now() - timedelta(hours=1),
        )
        response = client.post("/api/v1/seasons/2007/santa_chat")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Этот сезон находится в архиве"
        )
        Season.objects.filter(pk=2007).update(
            season_close=timezone.now() + timedelta(hours=1),
        )
        response = client.post("/api/v1/seasons/2007/santa_chat")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Ой, а вы во всем этом и не участвуете"
        )
        participation = Participation.objects.create(
            season=season,
            user=user,
        )
        response = client.post("/api/v1/seasons/2007/santa_chat")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Вам еще не назначен Дед Мороз"
        )
        another_user = User.objects.create(login="kafeman")
        santa = Participation.objects.create(
            season=season,
            user=another_user,
            giftee=participation,
        )
        response = client.post("/api/v1/seasons/2007/santa_chat")
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(obj["text"], ["Обязательное поле."])
        response = client.post("/api/v1/seasons/2007/santa_chat", {
            "text": "Hello World",
        })
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["text"], "Hello World")
        self.assertTrue(obj["is_author"])
        msg = Message.objects.get(sender=participation, recipient=santa)
        self.assertEqual(msg.text, "Hello World")

    def test_mark_delivered(self):
        client = APIClient()
        response = client.post("/api/v1/seasons/2007/mark_delivered")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.post("/api/v1/seasons/2007/mark_delivered")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        season = Season.objects.create(
            id=2007,
            registration_open=timezone.now() - timedelta(hours=3),
            registration_close=timezone.now() - timedelta(hours=2),
            season_close=timezone.now() - timedelta(hours=1),
        )
        response = client.post("/api/v1/seasons/2007/mark_delivered")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Этот сезон находится в архиве"
        )
        Season.objects.filter(pk=2007).update(
            season_close=timezone.now() + timedelta(hours=1),
        )
        response = client.post("/api/v1/seasons/2007/mark_delivered")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Ой, а вы во всем этом и не участвуете"
        )
        participation = Participation.objects.create(
            season=season,
            user=user,
        )
        response = client.post("/api/v1/seasons/2007/mark_delivered")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Вам еще не назначен Дед Мороз"
        )
        another_user = User.objects.create(login="kafeman")
        santa = Participation.objects.create(
            season=season,
            user=another_user,
            giftee=participation,
        )
        response = client.post("/api/v1/seasons/2007/mark_delivered")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Нельзя получить подарок до того, как он был отправлен"
        )
        santa.gift_shipped_at = timezone.now()
        santa.save()
        response = client.post("/api/v1/seasons/2007/mark_delivered")
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["season"]["id"], 2007)
        self.assertEqual(obj["season"]["delivered_count"], 1)
        self.assertIsNotNone(obj["participation"]["gift_delivered_at"])
        response = client.post("/api/v1/seasons/2007/mark_delivered")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Вами уже был получен один подарок"
        )

    def test_mark_shipped(self):
        client = APIClient()
        response = client.post("/api/v1/seasons/2007/mark_shipped")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.post("/api/v1/seasons/2007/mark_shipped")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        season = Season.objects.create(
            id=2007,
            registration_open=timezone.now() - timedelta(hours=3),
            registration_close=timezone.now() - timedelta(hours=2),
            season_close=timezone.now() - timedelta(hours=1),
        )
        response = client.post("/api/v1/seasons/2007/mark_shipped")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Этот сезон находится в архиве"
        )
        Season.objects.filter(pk=2007).update(
            season_close=timezone.now() + timedelta(hours=1),
        )
        response = client.post("/api/v1/seasons/2007/mark_shipped")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Ой, а вы во всем этом и не участвуете"
        )
        participation = Participation.objects.create(
            season=season,
            user=user,
        )
        response = client.post("/api/v1/seasons/2007/mark_shipped")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Вам еще не назначен получателя подарка"
        )
        another_user = User.objects.create(login="kafeman")
        giftee = Participation.objects.create(
            season=season,
            user=another_user,
        )
        participation.giftee = giftee
        participation.save()
        response = client.post("/api/v1/seasons/2007/mark_shipped")
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["season"]["id"], 2007)
        self.assertEqual(obj["season"]["shipped_count"], 1)
        self.assertIsNotNone(obj["participation"]["gift_shipped_at"])
        response = client.post("/api/v1/seasons/2007/mark_shipped")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Вами уже был отправлен один подарок"
        )

    def test_participation(self):
        client = APIClient()
        response = client.get("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.get("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        season = Season.objects.create(
            id=2007,
            registration_open=timezone.now() - timedelta(hours=3),
            registration_close=timezone.now() - timedelta(hours=2),
            season_close=timezone.now() - timedelta(hours=1),
        )
        response = client.get("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Ой, а вы во всем этом и не участвуете"
        )
        participation = Participation.objects.create(
            season=season,
            user=user,
            fullname="Kafe Man",
            postcode="12345",
            address="Kafeman St. 42\nKafecity",
            country="AL",
        )
        response = client.get("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["fullname"], "Kafe Man")
        self.assertEqual(obj["postcode"], "12345")
        self.assertEqual(obj["address"], "Kafeman St. 42\nKafecity")
        self.assertEqual(obj["country"], "AL")
        self.assertIsNone(obj["gift_shipped_at"])
        self.assertIsNone(obj["gift_delivered_at"])
        self.assertIsNone(obj["giftee"])
        self.assertIsNone(obj["santa"])

    def test_create_participation(self):
        client = APIClient()
        response = client.post("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.post("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        season = Season.objects.create(
            id=2007,
            registration_open=timezone.now() - timedelta(hours=3),
            registration_close=timezone.now() - timedelta(hours=2),
            season_close=timezone.now() - timedelta(hours=1),
        )
        response = client.post("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Этот сезон находится в архиве"
        )
        Season.objects.filter(pk=2007).update(
            season_close=timezone.now() + timedelta(hours=2),
        )
        response = client.post("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Регистрация на этот сезон уже невозможна"
        )
        Season.objects.filter(pk=2007).update(
            registration_close=timezone.now() + timedelta(hours=1),
        )
        # Trick the code by setting some fake data in the cache...
        cache.set("profile:exploitable", {
            "karma": 0,
            "has_badge": False,
            "is_readonly": False,
        }, 5)
        response = client.post("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Вы не можете участвовать в нашем клубе"
        )
        user = User.objects.create(login="kafeman")
        client.force_authenticate(user=user)
        # Trick the code by setting some fake data in the cache...
        cache.set("profile:kafeman", {
            "karma": 100,
            "has_badge": True,
            "is_readonly": False,
        }, 5)
        response = client.post("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(obj["fullname"], ["Обязательное поле."])
        self.assertEqual(obj["postcode"], ["Обязательное поле."])
        self.assertEqual(obj["address"], ["Обязательное поле."])
        self.assertEqual(obj["country"], ["Обязательное поле."])
        response = client.post("/api/v1/seasons/2007/participation", {
            "fullname": "Kafe Man",
            "postcode": "12345",
            "address": "Kafeman St. 42\nKafecity",
            "country": "AL",
        })
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["season"]["id"], 2007)
        self.assertEqual(obj["season"]["member_count"], 1)
        self.assertEqual(obj["participation"]["fullname"], "Kafe Man")
        self.assertEqual(obj["participation"]["postcode"], "12345")
        self.assertEqual(obj["participation"]["address"], "Kafeman St. 42\nKafecity")
        self.assertEqual(obj["participation"]["country"], "AL")
        response = client.post("/api/v1/seasons/2007/participation", {
            "fullname": "Kafe Man",
            "postcode": "12345",
            "address": "Kafeman St. 42\nKafecity",
            "country": "AL",
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Вы уже зарегистрированы на этот сезон"
        )

    def test_cancel_participation(self):
        client = APIClient()
        response = client.delete("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.delete("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        season = Season.objects.create(
            id=2007,
            registration_open=timezone.now() - timedelta(hours=3),
            registration_close=timezone.now() - timedelta(hours=2),
            season_close=timezone.now() - timedelta(hours=1),
        )
        response = client.delete("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Этот сезон находится в архиве"
        )
        Season.objects.filter(pk=2007).update(
            season_close=timezone.now() + timedelta(hours=2),
        )
        response = client.delete("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Ой, а вы во всем этом и не участвуете"
        )
        participation = Participation.objects.create(
            season=season,
            user=user,
        )
        response = client.delete("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Нельзя отказаться после окончания регистрации"
        )
        Season.objects.filter(pk=2007).update(
            registration_close=timezone.now() + timedelta(hours=1),
            member_count=1, # Otherwise member_count becomes negative.
        )
        response = client.delete("/api/v1/seasons/2007/participation")
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["season"]["id"], 2007)
        self.assertEqual(obj["season"]["member_count"], 0)
        self.assertIsNone(obj["participation"])

    def test_latest(self):
        client = APIClient()
        response = client.get("/api/v1/seasons/latest")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        Season.objects.create(
            id=2007,
            registration_open=timezone.now() - timedelta(hours=3),
            registration_close=timezone.now() - timedelta(hours=2),
            season_close=timezone.now() - timedelta(hours=1),
        )
        Season.objects.create(
            id=1991,
            registration_open=timezone.now() - timedelta(hours=3),
            registration_close=timezone.now() - timedelta(hours=2),
            season_close=timezone.now() - timedelta(hours=1),
        )
        response = client.get("/api/v1/seasons/latest")
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["id"], 2007)

    def test_countries(self):
        client = APIClient()
        response = client.get("/api/v1/seasons/2007/countries")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        Season.objects.create(
            id=2007,
            registration_open=timezone.now() - timedelta(hours=3),
            registration_close=timezone.now() - timedelta(hours=2),
            season_close=timezone.now() - timedelta(hours=1),
        )
        response = client.get("/api/v1/seasons/2007/countries")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"{}")
        # TODO: add more tests...


class UserViewSetTestCase(TestCase):
    def test_list(self):
        client = APIClient()
        response = client.get("/api/v1/users")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.get("/api/v1/users")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "У вас недостаточно прав для выполнения данного действия."
        )
        # TODO: We're not interested in this method now,
        # so just make sure normal users cannot access it...

    def test_retrieve(self):
        client = APIClient()
        response = client.get("/api/v1/users/exploitable")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.get("/api/v1/users/exploitable")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "У вас недостаточно прав для выполнения данного действия."
        )
        # TODO: We're not interested in this method now,
        # so just make sure normal users cannot access it...

    def test_ban(self):
        client = APIClient()
        response = client.post("/api/v1/users/negasus/ban")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.post("/api/v1/users/negasus/ban")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "У вас недостаточно прав для выполнения данного действия."
        )
        user = User.objects.create(login="kafeman")
        client.force_authenticate(user=user)
        response = client.post("/api/v1/users/negasus/ban")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        response = client.post("/api/v1/users/kafeman/ban")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Не стоит банить самого себя (потеряете доступ в админку!)"
        )
        User.objects.create(login="negasus")
        response = client.post("/api/v1/users/negasus/ban")
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(obj["reason"], ["Обязательное поле."])
        response = client.post("/api/v1/users/negasus/ban", {
            "reason": "just for fun",
        })
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["reason"], "just for fun")
        self.assertTrue(obj["is_banned"])
        response = client.post("/api/v1/users/negasus/ban")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Пользователь 'negasus' уже в бане"
        )

    def test_unban(self):
        client = APIClient()
        response = client.post("/api/v1/users/negasus/unban")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.post("/api/v1/users/negasus/unban")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "У вас недостаточно прав для выполнения данного действия."
        )
        user = User.objects.create(login="kafeman")
        client.force_authenticate(user=user)
        response = client.post("/api/v1/users/negasus/unban")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Страница не найдена."
        )
        User.objects.create(login="negasus")
        response = client.post("/api/v1/users/negasus/unban", {
            "reason": "sorry, that was enough fun",
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Пользователь 'negasus' уже разбанен"
        )
        User.objects.filter(login="negasus").update(is_banned=True)
        response = client.post("/api/v1/users/negasus/unban")
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(obj["reason"], ["Обязательное поле."])
        response = client.post("/api/v1/users/negasus/unban", {
            "reason": "sorry, that was enough fun",
        })
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["reason"], "sorry, that was enough fun")
        self.assertFalse(obj["is_banned"])

    def test_ban_history(self):
        client = APIClient()
        response = client.get("/api/v1/users/exploitable/ban_history")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.get("/api/v1/users/exploitable/ban_history")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "У вас недостаточно прав для выполнения данного действия."
        )
        # TODO: We're not interested in this method now,
        # so just make sure normal users cannot access it...

    def test_events(self):
        client = APIClient()
        response = client.get("/api/v1/users/exploitable/events")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.get("/api/v1/users/exploitable/events")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "У вас недостаточно прав для выполнения данного действия."
        )
        # TODO: We're not interested in this method now,
        # so just make sure normal users cannot access it...

    def test_send_email(self):
        client = APIClient()
        response = client.post("/api/v1/users/exploitable/send_email")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.post("/api/v1/users/exploitable/send_email")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "У вас недостаточно прав для выполнения данного действия."
        )
        # TODO: We're not interested in this method now,
        # so just make sure normal users cannot access it...

    def test_notification(self):
        client = APIClient()
        response = client.post("/api/v1/users/exploitable/send_notification")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.post("/api/v1/users/exploitable/send_notification")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "У вас недостаточно прав для выполнения данного действия."
        )
        # TODO: We're not interested in this method now,
        # so just make sure normal users cannot access it...


class CountryViewSetTestCase(TestCase):
    def test_list(self):
        client = APIClient()
        response = client.get("/api/v1/countries")
        self.assertEqual(response.status_code, 200)
        array = json.loads(response.content)
        self.assertEqual(array[0]["code"], "AU")
        self.assertEqual(array[0]["name"], "Австралия")


class EventViewSetTestCase(TestCase):
    def test_list(self):
        client = APIClient()
        response = client.get("/api/v1/events")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.get("/api/v1/events")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "У вас недостаточно прав для выполнения данного действия."
        )
        # TODO: We're not interested in this method now,
        # so just make sure normal users cannot access it...

    def test_retrieve(self):
        client = APIClient()
        response = client.get("/api/v1/events/1")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.get("/api/v1/events/1")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "У вас недостаточно прав для выполнения данного действия."
        )
        # TODO: We're not interested in this method now,
        # so just make sure normal users cannot access it...


class BackendViewTestCase(TestCase):
    def test_get(self):
        client = APIClient()
        response = client.get("/backend/info")
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertEqual(obj["is_authenticated"], False)
        self.assertEqual(obj["is_active"], False)
        self.assertEqual(obj["can_participate"], False)
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        # Trick the code by setting some fake data in the cache...
        cache.set("profile:exploitable", {
            "karma": 2,
            "has_badge": False,
            "is_readonly": False,
            "avatar_url": None,
        }, 5)
        response = client.get("/backend/info")
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertTrue(obj["is_authenticated"])
        self.assertTrue(obj["is_active"])
        self.assertFalse(obj["can_participate"])
        self.assertEqual(obj["username"], "exploitable")
        self.assertEqual(obj["avatar_url"], "https://hsto.org/storage/habrastock/i/avatars/stub-user-middle.gif")
        self.assertEqual(obj["karma"], 2)
        self.assertFalse(obj["is_readonly"])
        self.assertFalse(obj["has_badge"])


class MessageViewSetTestCase(TestCase):
    def test_mark_read(self):
        client = APIClient()
        response = client.post("/api/v1/messages/mark_read")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["detail"],
            "Учетные данные не были предоставлены."
        )
        user = User.objects.create(login="exploitable")
        client.force_authenticate(user=user)
        response = client.post("/api/v1/messages/mark_read", {
            "ids": [1, 2, 3],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["updated"], 0)
        # TODO: add more tests...
