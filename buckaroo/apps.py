from django.apps import AppConfig


class BuckarooConfig(AppConfig):
    name = 'buckaroo'

    def ready(self):
        from actstream import registry
        registry.register(self.get_model('Transaction'))
