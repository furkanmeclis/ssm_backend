from django.apps import AppConfig

class OgmMateryalConfig(AppConfig):
    name = 'ogmmateryal'
    verbose_name = 'OGM Materyal'

    def ready(self):
        from ogmmateryal import signals
