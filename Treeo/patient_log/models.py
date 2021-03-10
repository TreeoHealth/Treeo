from django.db import models
from users_acc.models import *
#blood_category ={
               #('red blood cells', 'red blood cells'),
                #('white blood cells', 'white blood cells'),
                #('platelets', 'platelets'),
                #('hemoglobin', 'hemoglobin'),
                #('hematocrit', 'hematocrit'),
                #}

class PatientLog(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True)
    calories = models.IntegerField(default=0)
    water = models.DecimalField(max_digits=5, decimal_places=2)
    sleep = models.DecimalField(max_digits=5, decimal_places=2)
    mood = models.IntegerField(default=5)
    date = models.DateTimeField(auto_now_add=True)



