from django.apps import AppConfig


class UploadDownloadConfig(AppConfig):
    name = 'upload_download'
    def ready(self):
        import upload_download.signals
