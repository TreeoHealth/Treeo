from django.db import models

# Create your models here.
class patientUser(models.Model):
    objects = models.Manager()
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    creation_date = models.DateTimeField('creation date')
    def usernameContainsA(self):
        return ('a' in str(self.username))
    def __str__(self): #makes the shell print username instead of object type
        return self.username
    
class providerUser(models.Model):
    objects = models.Manager()
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    creation_date = models.DateTimeField('creation date')
    
class appointmentObject(models.Model):
    objects = models.Manager()
    appointment_name = models.CharField(max_length=200)
    patient = models.ForeignKey(patientUser, on_delete=models.DO_NOTHING)
    provider = models.ForeignKey(providerUser,  on_delete=models.DO_NOTHING)
    startDate = models.DateTimeField('start date/time')