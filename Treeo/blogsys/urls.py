
from django.urls import path
from . import views

urlpatterns = [
    path('', views.Health_Coach, name='Health_Coach'),
    path('Provider', views.provider, name='provider'),
    path('Dietitian', views.dietitian, name='dietitian'),
    path('patient1', views.Patient1, name='Patient1'),
    path('patient2', views.Patient2, name='Patient2'),
    path('patient3', views.Patient3, name='Patient3'),
    path('patient4', views.Patient4, name='Patient4'),
    path('patient5', views.Patient5, name='Patient5'),
    path('patient6', views.Patient6, name='Patient6'),
    path('patient7', views.Patient7, name='Patient7'),
    path('patient8', views.Patient8, name='Patient8'),
    path('patient9', views.Patient9, name='Patient9'),
    path('patient10', views.Patient10, name='Patient10'),
    path('noassigned', views.noassigned, name='noassigned'),

]