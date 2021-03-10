from django.db.models.signals import post_save
from django.conf import settings
from django.dispatch import receiver
from users_acc.models import *


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def On_create_Patient(sender, instance, created, **kwargs):
    if created:
        if instance.is_superuser == True:
            Admin.objects.create(user=instance)
            instance.is_email_confirmed=1
            instance.save()
        # elif instance.user_type == 2:
        #     Provider.objects.create(user=instance)
        elif instance.user_type == 3:
            Patient.objects.create(user=instance)

