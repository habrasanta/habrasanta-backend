from django_celery_results.admin import TaskResultAdmin
from django_celery_results.models import TaskResult
from django.contrib import admin
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.http import urlencode

from habrasanta.models import Event, Participation, Season, User


class SeasonAdmin(admin.ModelAdmin): # type: ignore[type-arg]
    readonly_fields = ["address_match"]


class ParticipationInline(admin.StackedInline): # type: ignore[type-arg]
    model = Participation
    readonly_fields = ["country", "santa", "giftee", "gift_shipped_at", "gift_delivered_at"]
    extra = 0

    def get_exclude(self, request: HttpRequest, participation: Participation | None = None) -> list[str] | None:
        exclude = []
        if not request.user.has_perm("habrasanta.view_participation_address", participation):
            exclude += ["fullname", "postcode", "address"]
        return exclude


class UserAdmin(admin.ModelAdmin): # type: ignore[type-arg]
    inlines = [ParticipationInline]
    readonly_fields = [
        "is_banned",
        "first_login",
        "last_login",
        "last_online",
        "last_chat_notification",
        "habr_id",
    ]
    search_fields = ["login__iexact"]

    def get_readonly_fields(self, request: HttpRequest, user: User | None = None) -> list[str]:
        fields = list(self.readonly_fields)
        if request.user.has_perm("habrasanta.view_user_email", user):
            fields = ["email"] + fields
        return fields


class EventAdmin(admin.ModelAdmin): # type: ignore[type-arg]
    list_display = ["time", "typ", "sub", "season", "ip_address"]


class AdminSite(admin.AdminSite):
    site_header = "Хабра АДМ"

    def login(self, request: HttpRequest, extra_context: dict[str, object] | None = None) -> HttpResponse:
        if request.method == "GET" and self.has_permission(request):
            return HttpResponseRedirect(reverse("admin:index", current_app=self.name))
        login_url = reverse("login")
        if "next" in request.GET:
            login_url += "?" + urlencode({
                "next": request.GET["next"],
            })
        return HttpResponseRedirect(login_url)


site = AdminSite()
site.register(Season, SeasonAdmin)
site.register(User, UserAdmin)
site.register(Event, EventAdmin)
site.register(TaskResult, TaskResultAdmin)
