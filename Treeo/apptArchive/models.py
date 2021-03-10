from django.db import models
from ReqAppt.models import *

class ApptArchive(models.Model):
    apptId = models.AutoField(primary_key=True)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, null=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True)
    meetingDate = models.DateTimeField(auto_now=False, null=True)

class Notes(models.Model):
    notes = models.CharField(max_length=600)
    apptId = models.ForeignKey(ApptArchive, on_delete=models.CASCADE)
    #dateAdded = models.DateTimeField(auto_now=True)

