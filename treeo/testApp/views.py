from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

#like a flask endpoint (function that is called by some action/link in the testApp urls conf file)
def index(request): 
    return HttpResponse("Hello, world. You're at the index.")

def patient1(request, patient_id):
    return HttpResponse("You're looking at patient %s (1)." % patient_id)

def patient2(request, patient_id):
    response = "You're looking at patient %s (2)."
    return HttpResponse(response % patient_id)

def patient3(request, patient_id):
    return HttpResponse("You're looking at patient %s (3)." % patient_id)