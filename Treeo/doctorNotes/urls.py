from django.urls import path
from . import views

urlpatterns = [
        path('', views.index, name='index'), #calls index (no ()s needed)
        path('create_new/', views.create_new_note, name='create_note'), #calls index (no ()s needed)
]