from django.apps import AppConfig


class OpportunitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opportunities'

    def ready(self):
        import opportunities.signals  # noqa: F401
