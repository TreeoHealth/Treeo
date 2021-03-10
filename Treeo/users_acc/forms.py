from django import forms
from django.conf import settings
from .models import *
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db.models import Q


class CustomModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, object):
        return object.user.get_full_name()


class CustomProviderModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, object):
        return object.user.get_full_name() + " "+str(object.Patient_count)+" Patients"


class PatientRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    phone_no = PhoneNumberField(blank=True, null=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password1',
                  'password2', 'first_name', 'last_name', 'phone_no']

        def save(self, commit=True):
            user = super(PatientRegisterForm, self).save(commit=False)
            user.email = self.cleaned_data['email']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.user_type = 3
            if commit:
                user.save()
            return user


CHOICES = [
    (1, 'Physician'),
    (2, 'Dietician'),
    (3, 'Coach'),
]


class ProviderRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    providertype = forms.IntegerField(
        label='What Type of Provider are You?', widget=forms.Select(choices=CHOICES))
    phone_no = PhoneNumberField(blank=True, null=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password1',
                  'password2', 'first_name', 'last_name', 'phone_no']
        exclude = ('user_type',)

        def save(self, commit=True):
            user = super(PatientRegisterForm, self).save(commit=False)
            user.email = self.cleaned_data['email']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.user_type = 2
            if commit:
                user.save()
            return user


class User_Update_Form(forms.ModelForm):
    username = forms.CharField(max_length=30)
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    phone_no = PhoneNumberField(blank=True, null=True)
    profile_pic = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name',
                  'last_name', 'phone_no', 'profile_pic']
        labels = {
            'phone_no': ('Phone Number'), 'last_name': ('Last Name'), 'first_name': ('First Name'),
        }
# some labels here for the html


# class TestForm(forms.Form):
#     pass

class AdminAssignForm(forms.Form):
    patient = CustomModelChoiceField(
        queryset=(Patient.objects.all()), empty_label="(Select a Patient)")


class AdminProviderUpdateForm(forms.ModelForm):
    # temp_id = forms.CharField()
    def __init__(self, *args, **kwargs):
        instance = kwargs.pop("instance")
        # super(ApptRequestForm, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        if instance.doc_d == None:
            self.fields['doc_d'].required = False
            self.fields['doc_d'] = CustomProviderModelChoiceField(queryset=(Provider.objects.filter(Patient_count__lt=10).filter(
                Provider_type=2)).order_by('Patient_count'), empty_label="(Select a Dietician)", required=False,)
        else:
            self.fields['doc_d'].initial = None
            self.fields['doc_d'].widget = forms.HiddenInput()
        if instance.doc_c == None:
            self.fields['doc_c'].required = False
            self.fields['doc_c'] = CustomProviderModelChoiceField(queryset=(Provider.objects.filter(Patient_count__lt=10).filter(
                Provider_type=3)).order_by('Patient_count'), empty_label="(Select a Coach)", required=False,)
        else:
            self.fields['doc_c'].initial = None
            self.fields['doc_c'].widget = forms.HiddenInput()
        if instance.doc_p == None:
            self.fields['doc_p'].required = False
            self.fields['doc_p'] = CustomProviderModelChoiceField(queryset=(Provider.objects.filter(Patient_count__lt=10).filter(
                Provider_type=1)).order_by('Patient_count'), empty_label="(Select a Physician)", required=False,)
        else:
            self.fields['doc_p'].initial = None
            self.fields['doc_p'].widget = forms.HiddenInput()
        # self.fields['temp_id'].initial = instance
        # self.fields['temp_id'].widget = forms.HiddenInput()

    class Meta:
        model = Patient
        fields = ['doc_d', 'doc_c', 'doc_p']
#             self.fields['doc_p'].widget = forms.HiddenInput()
#             # this custom chice field retuns fname and lanme not object id in dropdown
#             self.fields['provider'] = CustomModelChoiceField(providers, empty_label="(Select a Provider)")
#             # sets value
#             self.fields['patient'].initial = instance.patient
#             # hides field
#             self.fields['patient'].widget = forms.HiddenInput()
#         else:
# doc_p = forms.ModelChoiceField(queryset=(Provider.objects.filter(Patient_count__lt=10).filter(Provider_type=1)), empty_label="(Select a Physician)")
# doc_d = forms.ModelChoiceField(queryset=(Provider.objects.filter(Patient_count__lt=10).filter(Provider_type=2)), empty_label="(Select a Dietician)")
# doc_c = forms.ModelChoiceField(queryset=(Provider.objects.filter(Patient_count__lt=10).filter(Provider_type=3)), empty_label="(Select a Coach)")
# if not (instance.patient.doc_d == None and instance.patient.doc_p == None and instance.patient.doc_c == None):
#     g = Provider.objects.filter(Q(id=instance.patient.doc_d.id) | Q(id=instance.patient.doc_p.id) | Q(id=instance.patient.doc_c.id))
# else:
#     # make empty set so no error on look up of .id
#     g = Provider.objects.none()
# # this custom chice field retuns fname and lanme not object id in dropdown
# self.fields['provider'] = CustomModelChoiceField(g)
