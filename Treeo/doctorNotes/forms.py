from .models import NotesObj
from django import forms

class NotesForm(forms.Form):
    notes = forms.CharField(max_length=600)
    dateAdded = forms.DateTimeField()
    class Meta:
        model = NotesObj
        fields = '__all__'
