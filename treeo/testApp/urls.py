from django.urls import path


from . import views #imports the index () function from views.py

urlpatterns = [
    # ex: /test_Url/
    path('', views.index, name='index'), #calls index (no ()s needed)
        #http://127.0.0.1:8000/test_Url/ (but if you change treeo urls.py to be "testurl", then 
        #   this becomes /testurl/ )
    # ex: /test_Url/5/
    path('<int:patient_id>/', views.patient1, name='patient1'),
    # ex: /test_Url/5/patient/
    path('<int:patient_id>/patient/', views.patient2, name='patient2'),
    # ex: /test_Url/5/pat/
    path('<int:patient_id>/pat/', views.patient3, name='patient3'),
]