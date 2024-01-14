from django.conf import settings
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers

from habrasanta import admin, views


router = routers.SimpleRouter(trailing_slash=False)
router.include_format_suffixes = False
router.register("countries", views.CountryViewSet, basename="country")
router.register("events", views.EventViewSet)
router.register("messages", views.MessageViewSet)
router.register("seasons", views.SeasonViewSet)
router.register("users", views.UserViewSet)

urlpatterns = [
    path("api/v1/", include(router.urls)),
    path("backend/login", views.LoginView.as_view(), name="login"),
    path("backend/login/callback", views.CallbackView.as_view(), name="callback"),
    path("backend/logout", views.LogoutView.as_view(), name="logout"),
    path("backend/info", views.InfoView.as_view(), name="userinfo"),
    path("backend/unsubscribe", views.UnsubscribeView.as_view(), name="unsubscribe"),
    path("backend/health", views.HealthView.as_view(), name="health"),
    path("django_admin/", admin.site.urls),
    path("api/schema", SpectacularAPIView.as_view(), name="schema"),
    path("api/explorer", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += [
        path("backend/fake_authorize", views.FakeAuthorizeView.as_view(), name="fake_authorize"),
    ]
