  
from django.db import models
from django.contrib.auth import get_user_model
from apptArchive.models import *
# Create your models here.
class NotesObj(models.Model):
    apptId =  models.AutoField(primary_key=True) ###ForeignKey(ApptArchive, on_delete=models.CASCADE) 
         #appt archive has patient/provider/etc.
    notes = models.CharField(max_length=600)
    isOriginalNote = models.BooleanField() 
    dateAdded = models.DateTimeField()