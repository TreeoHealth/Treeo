from django.contrib import admin

# Register your models here.

from .models import patientUser

admin.site.register(patientUser) #adds the contents of this model in the admin interface