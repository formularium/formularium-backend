from django.apps import AppConfig


class TeamsConfig(AppConfig):
    name = "teams"

    def register_signals(self):
        from . import signals

    def ready(self):
        self.register_signals()
