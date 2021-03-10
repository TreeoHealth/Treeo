from django.shortcuts import render, redirect
from apptArchive.models import ApptArchive, Notes
from apptArchive.forms import NotesForm

def view_archived_appointments(request):
    # query appointment table or notes after they select a n appointment request.user
    if request.user.user_type == 3:
        apptArchive=ApptArchive.objects.filter( patient=request.user.patient).order_by('meetingDate')
        return render(request, 'apptArchive/apptArchive.html', {'apptArchive': apptArchive})
    elif request.user.user_type == 2:
        apptArchive = ApptArchive.objects.filter(provider=request.user.provider).order_by('meetingDate')
        return render(request, 'apptArchive/apptArchive.html', {'apptArchive': apptArchive})
    else:
        redirect('home')

def view_archived_appointment(request,id):
    # the view for the one appointment and all of the notes on it
    if request.user.user_type == 3:
        apptArchive=ApptArchive.objects.filter( patient=request.user.patient).order_by('meetingDate')
        return render(request, 'apptArchive/apptArchive.html', {'apptArchive': apptArchive})
    elif request.user.user_type == 2:
        apptArchive = ApptArchive.objects.filter(provider=request.user.provider).order_by('meetingDate')
        return render(request, 'apptArchive/apptArchive.html', {'apptArchive': apptArchive})
    else:
        redirect('home')

#def create_note(request, id):
#    if request.user.user_type == 2:
#       if request.method =="POST":
  #          form = NotesForm(request.POST)
   #         if form.is_valid():
    #            saveNote = form.save()
     #           return render(request, 'notes.html', {"form": saveNote})
      #  else:
       #     return render(request, 'notes.html', {"form": NotesForm()})
        # is valid()
        # link it to the the archived apointment