from django.apps import AppConfig


class UsersAccConfig(AppConfig):
    name = 'users_acc'
    def ready(self):
        import users_acc.signals