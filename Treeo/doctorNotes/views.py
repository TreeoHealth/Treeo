from django.shortcuts import render, redirect
from apptArchive.models import ApptArchive
from doctorNotes.forms import NotesForm
from doctorNotes.models import NotesObj
from datetime import datetime, date, timedelta

# Create your views here.
def index(request): 
    all_dr_notes = NotesObj.objects.all()
    return render(request, 'doctorNotes/index.html', { 'all_dr_notes': all_dr_notes })

def create_new_note(request):
    if request.method == 'POST':
        form = NotesForm(request.POST)
        noteContent = request.POST['notes']
        creationDate = date.today().strftime("%Y-%m-%d");
        noteObj = NotesObj(
            #apptId = 2,
            notes = noteContent,
            dateAdded = creationDate,
            isOriginalNote=True
        )
        noteObj.save()
        all_dr_notes = NotesObj.objects.all()
        return render(request, 'doctorNotes/index.html', { 'all_dr_notes': all_dr_notes })
    else:
        return render(request, 'doctorNotes/createNote.html', {'form': NotesForm()})