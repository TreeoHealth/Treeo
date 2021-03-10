from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_archived_appointments, name='apptArchive'),
    path('archived_appointment/<id>', views.view_archived_appointment, name='archived_appointment'),
    #path('notes/<id>', views.create_note, name='notes'),

]