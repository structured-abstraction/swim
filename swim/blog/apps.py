from django.apps import AppConfig

class BlogAppConfig(AppConfig):
    name = 'swim.blog'

    def ready(self):
        from swim.blog import sitemaps
