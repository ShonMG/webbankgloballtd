from django.apps import AppConfig


class WebbankboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webbankboard'

    def ready(self):
        import webbankboard.signals # noqa F401
