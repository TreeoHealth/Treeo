from django.core.exceptions import MultipleObjectsReturned
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import *
from django.db.models import Sum
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
# Mail
from smtplib import SMTP
from django.core.mail import send_mail, EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from messaging.models import *
from patient_log.models import *
from blogsys.models import *
from ReqAppt.models import *

def register(request):
    if request.method == 'POST':
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            m = form.save()
            current_site = get_current_site(request)
            subject = 'Welcome to Treeo'
            message = render_to_string('users_acc/account_activation_email.html', {
                'user': form.cleaned_data.get('username'),
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(m.id)),
                'token': account_activation_token.make_token(m),
            })
            #print(subject, message, settings.EMAIL_HOST_USER, m.email)
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [m.email],
                fail_silently=False,
            )
            #m.email_user(subject, message)
            return redirect('account_activation_sent')
            # some logic to make sure its actually sent
            # return render(request, 'account_activation_sent.html')
        else:
            return render(request, 'users_acc/register.html', {'form': form})
    else:
        return render(request, 'users_acc/register.html', {'form': PatientRegisterForm()})


def account_activation_sent(request):
    return render(request, 'users_acc/account_activation_sent.html')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        print(uid)
        user = get_user_model().objects.get(id=uid)
    except (TypeError, ValueError, OverflowError,  get_user_model().DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        #user.is_active = True
        user.is_email_confirmed = True
        user.save()
        # m=message.objects.create()
        # m.sender = user
        # m.reciever = user
        # m.subject ='Welcome to Treeo'
        # m.convoID = 1
        # m.read_status = False
        # m.sender_loc = 'Outbox'
        # m.reciever_loc = 'Inbox'
        # m.msgbody = 'Welcome to Treeo'
        # m.save()
        login(request, user)
        return render(request, 'users_acc/account_activation_success.html')
    else:
        return render(request, 'users_acc/account_activation_invalid.html')


def button(request):
    if request.method == 'POST':
        #m = get_user_model().objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
        m=message.objects.create()
        m.sender = request.user
        m.reciever = request.user
        m.subject ='test'
        m.convoID = 1
        m.read_status = False
        m.sender_loc = 'Outbox'
        m.reciever_loc = 'Inbox'
        m.save()
        return redirect('button')
    else:
        return render(request, 'users_acc/button.html')


def loginuser(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        # print(username,password)
        # email or username code need acompying code in model or backend manager to stop @ being used in usernames
        # try:
        #     user = get_user_model().objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        # except get_user_model().DoesNotExist:
        #     get_user_model().set_password(password)
        # except MultipleObjectsReturned:
        #     return get_user_model().objects.filter(email=username).order_by('id').first()
        # else:
        #     if user.check_password(password) and self.user_can_authenticate(user):
        #         return user
        # try:
        #     user = get_user_model().objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        userl = authenticate(request, username=username, password=password)
        if userl is not None:
            # print("test1")
            if userl.is_email_confirmed == True:
                # print("test2")
                login(request, userl)
                # get the stuff or the get responce theing here

                return redirect('home')

                return redirect(request.POST.get('next')or request.GET.get('next') or 'home')

            else:
                return render(request, 'users_acc/login.html', {'form': AuthenticationForm(), 'errorMsg': 'Your Account Is Not Confirmed'})
        else:
            return render(request, 'users_acc/login.html', {'form': AuthenticationForm(), 'errorMsg': 'Username and password did not match'})
    else:
        return render(request, 'users_acc/login.html', {'form': AuthenticationForm()})


@login_required
def profile(request):
    return render(request, 'users_acc/profile.html')
    # this would be required if you dont use @login_required
    # if request.user.is_authenticated:
    # return render(request, 'profile.html')
    # else:
    #     return redirect('/login/?next=%s' % request.path)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        #form = User_Update_Form(request.POST or None)
        ep = User_Update_Form(request.POST, request.FILES, instance=request.user)
        if ep.is_valid():
            request.user.username = ep.cleaned_data.get("username")
            request.user.email = ep.cleaned_data.get("email")
            request.user.first_name = ep.cleaned_data.get("first_name")
            request.user.last_name = ep.cleaned_data.get("last_name")
            request.user.phone_no = ep.cleaned_data.get("phone_no")
            request.user.profile_pic = ep.cleaned_data.get("profile_pic")
            request.user.save()
            #print("test")
            # ep.save()
            #
            return redirect('profile')
        else:
            #print some error for validation of stuff
            #print(ep.errors)
            form = User_Update_Form(instance=request.user)
            return render(request, 'users_acc/edit_profile.html', {'edit_profile': form,'formerrors': ep})
    else:
        ep = User_Update_Form(instance=request.user)
    return render(request, 'users_acc/edit_profile.html', {'edit_profile': ep})


def doctor_registration(request):
    if request.method == 'POST':
        form = ProviderRegisterForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.user_type = 2
            m.save()
            e = Provider.objects.create(
                user=m, Provider_type=form.cleaned_data.get('providertype'))
            e.save()
            current_site = get_current_site(request)
            subject = 'Welcome to Treeo'
            message = render_to_string('users_acc/account_activation_email.html', {
                'user': form.cleaned_data.get('username'),
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(m.id)),
                'token': account_activation_token.make_token(m),
            })
            #print(subject, message, settings.EMAIL_HOST_USER, m.email)
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [m.email],
                fail_silently=False,
            )
            #m.email_user(subject, message)
            return redirect('account_activation_sent')
            # some logic to make sure its actually sent
            # return render(request, 'account_activation_sent.html')
        else:
            return render(request, 'users_acc/register_provider.html', {'form': form})
    else:
        return render(request, 'users_acc/register_provider.html', {'form': ProviderRegisterForm()})


@login_required
def admin_display_team(request, id):
    try:
        patient = Patient.objects.get(id=id)
    except Exception as e:
        print(e)
        return render(request, "users_acc/admin_assign.html", {'form': AdminAssignForm()})
    else:
        if request.method == 'POST':
            if 'doc_d' in request.POST and not request.POST['doc_d'] == '':
                try:
                    doc = get_object_or_404(Provider, id=request.POST['doc_d'])
                    patient.doc_d = doc
                    patient.save()
                    doc.Patient_count += 1
                    doc.save()
                except:
                    pass
            else:
                pass
            if 'doc_p' in request.POST and not request.POST['doc_p'] == '':
                try:
                    doc = get_object_or_404(Provider, id=request.POST['doc_p'])
                    patient.doc_p = doc
                    patient.save()
                    doc.Patient_count += 1
                    doc.save()
                except:
                    pass
            else:
                pass
            if 'doc_c' in request.POST and not request.POST['doc_c'] == '':
                try:
                    doc = get_object_or_404(Provider, id=request.POST['doc_c'])
                    patient.doc_c = doc
                    patient.save()
                    doc.Patient_count += 1
                    doc.save()
                except:
                    pass
            else:
                pass
            return render(request, "users_acc/admin_display_team.html", {'form': AdminProviderUpdateForm(instance=patient), 'patient': patient})
        else:
            return render(request, "users_acc/admin_display_team.html", {'form': AdminProviderUpdateForm(instance=patient), 'patient': patient})


@login_required
def admin_view(request):
    if request.method == 'POST':
        form = AdminAssignForm(request.POST)
        if form.is_valid():
            patient = Patient.objects.none()
            try:
                patient = Patient.objects.get(id=request.POST['patient'])
            except Exception as e:
                print(e)
                return render(request, "users_acc/admin_assign.html", {'form': AdminAssignForm()})
            else:
                return redirect('admin_display_team', request.POST['patient'])
        else:
            return render(request, "users_acc/admin_assign.html", {'form': AdminAssignForm(),'formerrors': form})
    else:
        return render(request, "users_acc/admin_assign.html", {'form': AdminAssignForm()})


def admin_remove_provider(request, id, id2):
    if request.method == "POST":
        # id = patient id2 =provider
        pat = get_object_or_404(Patient, id=id)
        doc = get_object_or_404(Provider, id=id2)
        if doc.Provider_type == 1:
            pat.doc_p = None
            pat.save()
            doc.Patient_count -= 1
            doc.save()
        if doc.Provider_type == 2:
            pat.doc_d = None
            pat.save()
            doc.Patient_count -= 1
            doc.save()
        if doc.Provider_type == 3:
            pat.doc_c = None
            pat.save()
            doc.Patient_count -= 1
            doc.save()
        return redirect('admin_display_team', pat.id)
    context = {'patient': id, 'provider': id2}
    return render(request, "users_acc/deleteconfirm.html", context)

@login_required
def admin_approve_provider_render(request):
    temp=Provider.objects.filter().order_by('is_verified')
    return render(request, "users_acc/admin_approve_provider.html", {'results': temp})

@login_required
def admin_approve_provider(request, id):
    try:
        temp = Provider.objects.get(id=id)
    except Exception as e:
        print(e)
        return redirect("admin_approve_provider_render")
    else:
        temp.is_verified=True
        temp.save()
    return redirect("admin_approve_provider_render")

@login_required
def admin_revoke_provider(request, id):
    try:
        temp = Provider.objects.get(id=id)
    except Exception as e:
        print(e)
    else:
        temp.is_verified=False
        temp.save()
    return redirect("admin_approve_provider_render")

# def render_privider_list(request,pat_obj):
#     content = {}
#     context = {}
#     try:
#         patient = Patient.objects.get(id=pat_obj)
#         context['patient'] = patient
#     except Exception as e:
#         print(e)
#     else:
#         if not patient.doc_d == None:
#             context['doc_d'] = patient.doc_d
#         else:
#             new_fields = {}
#             new_fields['doc_d'] = CustomModelChoiceField(
#                 Provider.objects.filter(Patient_count__lt=10).filter(Provider_type=2))
#             DynamicForm = type('DynamicForm', (TestForm,), new_fields)
#             IngForm = DynamicForm(content)
#             context['field1'] = IngForm
#         if not patient.doc_c == None:
#             context['doc_c'] = patient.doc_c
#         else:
#             new_fields = {}
#             new_fields['doc_c'] = CustomModelChoiceField(
#                 Provider.objects.filter(Patient_count__lt=10).filter(Provider_type=3))
#             DynamicForm = type('DynamicForm', (TestForm,), new_fields)
#             IngForm = DynamicForm(content)
#             context['field2'] = IngForm
#         if not patient.doc_p == None:
#             context['doc_p'] = patient.doc_p
#         else:
#             new_fields = {}
#             new_fields['doc_p'] = CustomModelChoiceField(
#                 Provider.objects.filter(Patient_count__lt=10).filter(Provider_type=1))
#             DynamicForm = type('DynamicForm', (TestForm,), new_fields)
#             IngForm = DynamicForm()
#             #see if DynamicForm() works ??????????????????????????????????????????????????????????????????
#             context['field3'] = IngForm
#         return render(request, "users_acc/admin_display_team.html", context)
# def dynamic(request):
#     context = {}
#     content = {}
#     new_fields = {}
#     patient=Patient.objects.none()

    # if request.method == 'POST':
    #     if 'patient' in request.POST:
    #         try:
    #             patient = Patient.objects.get(id=patient)
    #         except Exception as e:
    #             print(e)
    #         else:
    #             # if (patient.doc_d == None or patient.doc_p == None or patient.doc_c == None):
    #             #     # trys not needer as query sets wont error out?
    #             #     try:
    #             #         if patient.doc_d == None:
    #             #             new_fields['providers_d'] = CustomModelChoiceField(Provider.objects.filter(Patient_count__lt=10).filter(Provider_type=2))
    #             #     except Exception as e:
    #             #         print(e)
    #             #     try:
    #             #         if patient.doc_c == None:
    #             #             # providers_c = providers_c | Provider.objects.filter(Patient_count__lt=10).filter(Provider_type=3)
    #             #             new_fields['providers_c'] = CustomModelChoiceField(
    #             #                 Provider.objects.filter(Patient_count__lt=10).filter(Provider_type=3))
    #             #     except Exception as e:
    #             #         print(e)
    #             #     try:
    #             #         if patient.doc_p == None:
    #             #             # providers_p = providers_p | Provider.objects.filter(Patient_count__lt=10).filter(Provider_type=1)
    #             #             new_fields['providers_p'] = CustomModelChoiceField(
    #             #                 Provider.objects.filter(Patient_count__lt=10).filter(Provider_type=1))
    #             #     except Exception as e:
    #             #         print(e)
    #                 # hides field that passes the patient as hidden field
    #                 #new_fields['patient2'] = CustomModelChoiceField(widget=forms.HiddenInput(),queryset =Patient.objects.filter(id=patient.id), initial={'field1': patient })
    #                 DynamicForm = type('DynamicForm', (TestForm,), new_fields)
    #                 IngForm = DynamicForm(content)
    #                 context['form2'] = IngForm
    #                 #context['form2'] = AdminProviderUpdateForm()
    #                 context['patient'] = patient
    #                 return render(request, "users_acc/admin_assign.html", context)
    #             else:
    #                 #all guys assigned
    #                 # DynamicForm = type('DynamicForm', (TestForm,), new_fields)
    #                 # IngForm = DynamicForm(content)
    #                 # context['form2'] = IngForm
    #                 context['messages'] = "All Doctors asigned"
    #                 context['form'] = AdminAssignForm()
    #                 return render(request, "users_acc/admin_assign.html", context)
    #     else:
    #         #need to pass an id of patient
    #         print(request.POST)
    #         patient = request.POST['patient2']
    #         try:
    #             patient = Patient.objects.get(id=patient)
    #         except Exception as e:
    #             print(e)
    #         else:
    #             if 'providers_d' in request.POST:
    #                 patient.doc_d = request.POST['providers_d']
    #             if 'providers_c' in request.POST:
    #                 patient.doc_c = request.POST['providers_c']
    #             if 'providers_p' in request.POST:
    #                 patient.doc_p = request.POST['providers_p']
    #             print(patient.doc_p,patient.doc_c,patient.doc_d)
    #         DynamicForm = type('DynamicForm', (TestForm,), new_fields)
    #         IngForm = DynamicForm(content)
    #         context['form2'] = IngForm
    #         context['form'] = AdminAssignForm()
    #         return render(request, "users_acc/admin_assign.html", context)
    # else:
    #     DynamicForm = type('DynamicForm', (TestForm,), new_fields)
    #     IngForm = DynamicForm(content)
    #     context['form2'] = IngForm
    #     context['form'] = AdminAssignForm()
    # return render(request, "users_acc/admin_assign.html", context)


def home(request):
    if request.user.is_authenticated:
        return render(request, 'users_acc/home.html')
    else:
        return redirect('login')


# def home2(request):
#     context={}
#     if request.user.is_authenticated:
#         context= {'appointment': "", 'message': "", }
#         results=PostQ.objects.filter(Thereciever=(request.user)).order_by('meetingDate')[:2]
#         if results.count() == 0:
#             print('no appointments')
#         if request.user.user_type==3:
#             results=ApptTable.objects.filter(patient=(request.user)).order_by('meetingDate')[:2]
#         if request.user.user_type==2:
#             results=ApptTable.objects.filter(provider=(request.user)).order_by('meetingDate')[:2]
#             if results.count() == 0:
#                 print('no appointments')
#             request.user.date_joined.date()
#         return render(request, 'users_acc/home.html', context)
#     else:
#         return redirect('login')
