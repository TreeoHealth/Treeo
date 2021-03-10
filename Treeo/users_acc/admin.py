from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

admin.site.register(User, UserAdmin)
admin.site.register(Admin)
admin.site.register(Provider)
admin.site.register(Patient)