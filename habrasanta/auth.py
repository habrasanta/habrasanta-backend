import requests

from django.conf import settings
from django.contrib.auth.backends import ModelBackend

from habrasanta.models import User
from habrasanta.utils import fetch_habr_profile


class PublicHabrBackend(ModelBackend):
    """
    Habr has a semi-public authentication API and a private one.

    This backend authenticates users using the Habr's semi-public API.
    """
    def authenticate(self, request, authorization_code=None):
        response = requests.post(settings.HABR_TOKEN_URL, data={
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": settings.HABR_CLIENT_ID,
            "client_secret": settings.HABR_CLIENT_SECRET,
        })
        if response.status_code != 200:
            return None
        data = response.json()
        access_token = data.get("access_token")
        profile = self.fetch_profile(access_token)
        if not profile:
            return None
        habr_id = profile.get("id")
        username = profile.get("alias")
        if not habr_id or not username:
            return None
        try:
            user = User.objects.get(habr_id=habr_id)
        except User.DoesNotExist:
            try:
                # Users registered before OAuth support existed might not have an ID.
                user = User.objects.get(login=username)
            except User.DoesNotExist:
                # This is the first time the user signs in.
                user = User(habr_id=habr_id)
        user.login = username
        user.email = profile.get("email")
        user.habr_id = habr_id
        user.habr_token = access_token
        user.save()
        return user

    def fetch_profile(self, access_token):
        if not access_token:
            return None
        response = requests.get(settings.HABR_USER_INFO_URL, headers={
            "client": settings.HABR_CLIENT_ID,
            "token": access_token,
        })
        if response.status_code != 200:
            return None
        return response.json()


class FakeBackend(ModelBackend):
    """
    This backend skips the authorization step during development, yet real Habr
    profiles are still used (make sure the environment variable HABR_APIKEY is set).
    """
    def authenticate(self, request, authorization_code=None):
        if not authorization_code:
            return None
        # Username is passed instead of the real authorization code.
        username = authorization_code
        profile = fetch_habr_profile(username)
        if not profile:
            return None
        try:
            user = User.objects.get(login=username)
        except User.DoesNotExist:
            user = User(login=username)
            user.save()
        return user
