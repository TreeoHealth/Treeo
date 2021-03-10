from django.shortcuts import render
from .models import patientUser
# Create your views here.
from django.http import Http404
from django.http import HttpResponse

#like a flask endpoint (function that is called by some action/link in the testApp urls conf file)
def index(request): 
    all_patients = patientUser.objects.all()
    
    context = {
        'all_patients': all_patients
    }
    return render(request, 'testApp/index.html', context)
    #template = loader.get_template('testApp/testApp/index.html')
    #return HttpResponse(template.render(context, request))

def patient1(request, patient_id):
    try:
        patient = patientUser.objects.get(pk=patient_id)
    except patientUser.DoesNotExist:
        raise Http404("Patient does not exist")
    return render(request, 'testApp/detail.html', {'patient': patient})

def patient2(request, patient_id):
    response = "You're looking at patient %s (2)."
    return HttpResponse(response % patient_id)

def patient3(request, patient_id):
    return HttpResponse("You're looking at patient %s (3)." % patient_id)