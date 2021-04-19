from django.apps import AppConfig


class FormsConfig(AppConfig):
    name = "forms"

    def register_signals(self):
        from . import signals

    def ready(self):
        self.register_signals()
