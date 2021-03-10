from django.db.models.signals import post_delete
from django.conf import settings
from django.dispatch import receiver
from upload_download.models import *



#only when an uploaded file is deleted
@receiver(post_delete, sender=Uploaded_File)
def uploaded_file_delete(sender, instance, **kwargs):
    instance.file.delete(False)

#  a more general implementaion where whenever any model is deleted, if it
#  has a file field the associated files are deleted too if it is not being used by another model
# @receiver(post_delete)
# def when_file_deleted(sender, instance, **kwargs):
#     for f in sender._meta.concrete_fields:
#         if isinstance(f,models.FileField):
#             file_field = getattr(instance,f.name)
#             delete_file_if_not_being_used(sender,instance,field,file_field)
# def delete_file_if_not_being_used(model,instance,field,file_field):
#     dynamic_field = {}
#     dynamic_field[field.name] = file_field.name
#     other_refs_exist = model.objects.filter(**dynamic_field).exclude(pk=instance.pk).exists()
#     if not other_refs_exist:
#         file_field.delete(False)