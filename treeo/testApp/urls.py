from django.urls import path

from . import views #imports the index () function from views.py

urlpatterns = [
    path('', views.index, name='index'), #calls index (no ()s needed)
        #http://127.0.0.1:8000/test_Url/ (but if you change treeo urls.py to be "testurl", then 
        #   this becomes /testurl/ )
]