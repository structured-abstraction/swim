from django.apps import AppConfig

class EventAppConfig(AppConfig):
    name = 'swim.event'

    def ready(self):
        from swim.event import sitemaps
