from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in, user_logged_out


class HabrasantaConfig(AppConfig):
    name = "habrasanta"
    verbose_name = "Хабра АДМ"

    def ready(self):
        from habrasanta import signals
        user_logged_in.connect(signals.log_user_login)
        user_logged_out.connect(signals.log_user_logout)
