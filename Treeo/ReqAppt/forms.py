from django import forms
from . import models
from .models import ApptTable
from users_acc.models import *
from django.db.models import Q
from users_acc.forms import CustomModelChoiceField

# class CustomModelChoiceField(forms.ModelChoiceField):
#     def label_from_instance(self, object):
#          return object.user.get_full_name()




class ApptRequestFormPatient(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop("instance")
        #super(ApptRequestForm, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        if instance.user_type == 2:
            q = Provider.objects.none()
            if instance.provider.Provider_type ==1:
                q = Patient.objects.filter(doc_p=instance.provider)
            elif instance.provider.Provider_type ==2:
                q = Patient.objects.filter(doc_d=instance.provider)
            elif instance.provider.Provider_type ==3:
                q = Patient.objects.filter(doc_c=instance.provider)
            self.fields['patient']=CustomModelChoiceField(q, empty_label="(Select a Patient)")
            #sets value
            self.fields['provider'].initial = instance.provider
            # hides field
            self.fields['provider'].widget = forms.HiddenInput()
            # self.fields['provider'] = instance.provider
        elif instance.user_type == 3:
            #if (instance.patient.doc_d!=None and instance.patient.doc_p!=None and instance.patient.doc_c!=None):
            providers = Provider.objects.none()
            if(instance.patient.doc_d==None or instance.patient.doc_p==None or instance.patient.doc_c==None):
                try:
                    providers = providers | Provider.objects.filter(id=instance.patient.doc_d.id)
                except Exception as e:
                    print(e)
                try:
                    providers = providers | Provider.objects.filter(id=instance.patient.doc_p.id)
                except Exception as e:
                    print(e)
                try:
                    providers = providers | Provider.objects.filter(id=instance.patient.doc_c.id)
                except Exception as e:
                    print(e)
            else:
                #make empty set so no error on look up of .id
                providers = Provider.objects.filter(Q(id=instance.patient.doc_d.id) | Q(id=instance.patient.doc_p.id) | Q(id=instance.patient.doc_c.id))
            #this custom chice field retuns fname and lanme not object id in dropdown
            self.fields['provider'] = CustomModelChoiceField(providers, empty_label="(Select a Provider)")
            #sets value
            self.fields['patient'].initial = instance.patient
            # hides field
            self.fields['patient'].widget = forms.HiddenInput()
        else:
            self.fields['patient'].label_from_instance = lambda p: f"{p.user.first_name} {p.user.last_name}"
            self.fields['provider'].label_from_instance = lambda p: f"{p.user.first_name} {p.user.last_name}"



    class Meta:
        model = ApptTable
        #fields = '__all__'
        exclude = ['meetingDate', 'status', 'meeturl']


# class ApptRequestForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         super(ApptRequestForm, self).__init__(*args, **kwargs)
#         self.fields['patient'].label_from_instance = lambda p: f"{p.user.first_name} {p.user.last_name}"
#         self.fields['provider'].label_from_instance = lambda p: f"{p.user.first_name} {p.user.last_name}"
#
#
#
#     class Meta:
#         model = ApptTable
#         #fields = '__all__'
#         exclude = ['meetingDate', 'status']