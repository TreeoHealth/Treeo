from django import forms


class Fileform(forms.Form):
    file = forms.FileField()