from django.apps import AppConfig

class ContentAppConfig(AppConfig):
    name = 'swim.content'

    def ready(self):
        from swim.content import sitemaps
