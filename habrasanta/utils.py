import requests
import time

from django.conf import settings
from django.core.cache import cache


session = requests.Session()
session.headers.update({
    "User-Agent": settings.HABR_USER_AGENT,
})


def fetch_habr_profile(username):
    profile = cache.get("profile:" + username)
    if not profile:
        start = time.time()
        response = session.get("https://habr.com/api/v2/users/{}/card".format(username), headers={
            "apikey": settings.HABR_APIKEY,
        }, timeout=(0.5, 0.4))
        if response.status_code != 200:
            return None
        card = response.json()
        response = session.get("https://habr.com/api/v2/users/{}/whois".format(username), headers={
            "apikey": settings.HABR_APIKEY,
        }, timeout=(0.5, 0.4))
        if response.status_code != 200:
            return None
        whois = response.json()
        end = time.time()
        print("Fetched Habr user '{}' in {:.3f} ms.".format(username, (end - start) * 1000))
        profile = {
            "avatar_url": card["avatarUrl"],
            "karma": card["scoreStats"]["score"],
            "has_badge": len([x for x in whois["badgets"] if x["title"] == "Дед Мороз"]) > 0,
            "is_readonly": card["isReadonly"],
        }
        cache.set("profile:" + username, profile, 60)
    return profile
