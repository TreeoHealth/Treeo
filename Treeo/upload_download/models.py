from django.db import models
from django.conf import settings
# Create your models here.

class Uploaded_File(models.Model):
    usern = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    #how long is max file name and is this the best way to store as var char has to aloctate 100 everytime
    file_name = models.CharField(max_length = 100)
    file = models.FileField(upload_to='uploaded_files')
    #make read only
    date_created = models.DateTimeField(auto_now_add=True)