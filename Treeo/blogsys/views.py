from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from blogsys.models import PostQ
from .forms import PostQform
from users_acc.models import *

# This First Function is a bit long due to it being called and used for bot patient and provider.
def Health_Coach(request):
    # If patient
    if request.user.user_type == 3:
        x = PostQ.objects.filter( Thereciever= (request.user.patient.user), Thesender=(request.user.patient.doc_c.user))
        if request.method == 'POST':
            form = PostQform(request.POST)

            if form.is_valid():
                save = PostQ()
                save.Message = form.cleaned_data.get('Message')
                save.Thereciever = (request.user.patient.user)
                save.TheActualsender=(request.user.patient.user)
                save.Thesender= (request.user.patient.doc_c.user)
                save.save()
                form = PostQform()

                if request.user.user_type == 3:
                    First = request.user.patient.doc_c.user.first_name
                    Last = request.user.patient.doc_c.user.last_name

                    return render(request, 'blogsys/Health_Coach.html',
                                {"form": form, 'PostQ': x, "First": First, "Last": Last})


                else:
                    return HttpResponseBadRequest()
        else:
            form = PostQform()
            if request.user.user_type == 3:
                if request.user.user_type == 3:
                    First = request.user.patient.doc_c.user.first_name
                    Last = request.user.patient.doc_c.user.last_name

                    return render(request, 'blogsys/Health_Coach.html',
                                {"form": form, 'PostQ': x, "First": First, "Last": Last})

    # If Provider Duplicated to get sender and receiver info
    if request.user.user_type == 2:
        if request.user.provider.Provider_type == 1:
            q = Patient.objects.filter(doc_p=request.user.provider)[0:]
        elif request.user.provider.Provider_type == 2:
            q = Patient.objects.filter(doc_d=request.user.provider)[0:]
        elif request.user.provider.Provider_type == 3:
            q = Patient.objects.filter(doc_c=request.user.provider)[0:]
        if request.method == 'POST':
            form = PostQform(request.POST)

            if form.is_valid():
                save = PostQ()
                save.Message = form.cleaned_data.get('Message')
                save.TheActualsender = (request.user.provider.user)
                save.Thesender = (request.user.provider.user)

                save.Thereciever = (q[0].user)
                save.save()
                form = PostQform()



                if request.user.user_type == 2:
                    if request.user.provider.Provider_type == 1:
                        q = Patient.objects.filter(doc_p=request.user.provider)[0:]
                    elif request.user.provider.Provider_type == 2:
                        q = Patient.objects.filter(doc_d=request.user.provider)[0:]
                    elif request.user.provider.Provider_type == 3:
                        q = Patient.objects.filter(doc_c=request.user.provider)[0:]

                    if len(q) >= 1:
                        x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
                        return render(request, 'blogsys/patient1.html', {"form": form, 'PostQ': x, "q": q[0]})
                    else:
                        return render(request, 'blogsys/noassigned.html')
                else:
                    return HttpResponseBadRequest()
        else:
            form = PostQform()

            if request.user.user_type == 2:
                if request.user.provider.Provider_type == 1:
                    q = Patient.objects.filter(doc_p=request.user.provider)[0:]
                elif request.user.provider.Provider_type == 2:
                    q = Patient.objects.filter(doc_d=request.user.provider)[0:]
                elif request.user.provider.Provider_type == 3:
                    q = Patient.objects.filter(doc_c=request.user.provider)[0:]

                if len(q) >= 1:
                    x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
                    return render(request, 'blogsys/patient1.html', {"form": form, 'PostQ': x, "q": q[0]})
                else:
                    return render(request, 'blogsys/noassigned.html')

def provider(request):

    x = PostQ.objects.filter(Thereciever=(request.user.patient.user), Thesender= (request.user.patient.doc_p.user))
    if request.method =='POST':
        form = PostQform(request.POST)
        if form.is_valid():
            save=PostQ()
            save.Message=form.cleaned_data.get('Message')
            save.Thereciever=(request.user.patient.user)
            save.Thesender = (request.user.patient.doc_p.user)
            save.TheActualsender = (request.user.patient.user)
            save.save()
            form = PostQform()
            First = request.user.patient.doc_p.user.first_name
            Last = request.user.patient.doc_p.user.last_name

            return render(request, 'blogsys/provider.html',
                          {"form": form, 'PostQ': x, "First": First, "Last": Last})
        else:

            return HttpResponseBadRequest()
    else:
        form = PostQform()
        First = request.user.patient.doc_p.user.first_name
        Last = request.user.patient.doc_p.user.last_name

        return render(request, 'blogsys/provider.html', {"form": form, 'PostQ': x, "First": First, "Last": Last})



def dietitian(request):
    x = PostQ.objects.filter(Thereciever = (request.user.patient.user),Thesender = (request.user.patient.doc_d.user))

    if request.method =='POST':
        form = PostQform(request.POST)

        if form.is_valid():

            save=PostQ()
            save.Message=form.cleaned_data.get('Message')
            save.Thereciever = (request.user.patient.user)
            save.TheActualsender = (request.user.patient.user)
            save.Thesender = (request.user.patient.doc_d.user)
            save.save()
            form=PostQform()
            First = request.user.patient.doc_d.user.first_name
            Last = request.user.patient.doc_d.user.last_name

            return render(request, 'blogsys/dietitian.html',
                          {"form": form, 'PostQ': x, "First": First, "Last": Last})
        else:

            return HttpResponseBadRequest()
    else:
        form = PostQform()
        First = request.user.patient.doc_d.user.first_name
        Last = request.user.patient.doc_d.user.last_name

        return render(request, 'blogsys/dietitian.html', {"form": form, 'PostQ': x, "First": First, "Last": Last})
def Patient1(request):
    if request.user.provider.Provider_type == 1:
        q = Patient.objects.filter(doc_p=request.user.provider)[0:]
    elif request.user.provider.Provider_type == 2:
        q = Patient.objects.filter(doc_d=request.user.provider)[0:]
    elif request.user.provider.Provider_type == 3:
        q = Patient.objects.filter(doc_c=request.user.provider)[0:]
    if request.method == 'POST':
        form = PostQform(request.POST)
        if form.is_valid():
            save = PostQ()
            save.Thesender = (request.user.provider.user)
            save.TheActualsender = (request.user.provider.user)
            save.Thereciever = (q[0].user)
            save.Message = form.cleaned_data.get('Message')
            save.save()
            form = PostQform()

            if len(q) >= 1:
                x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
                return render(request, 'blogsys/patient1.html', {"form": form, 'PostQ': x, "q": q[0]})
            else:
                return render(request, 'blogsys/noassigned.html')
        else:
            return HttpResponseBadRequest()
    else:
        form = PostQform()
        if len(q) >= 1:
            x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
            return render(request, 'blogsys/patient1.html', {"form": form, 'PostQ': x, "q": q[0]})
        else:
            return render(request, 'blogsys/noassigned.html')
def Patient2(request):
    if request.user.provider.Provider_type == 1:
        q = Patient.objects.filter(doc_p=request.user.provider)[1:]
    elif request.user.provider.Provider_type == 2:
        q = Patient.objects.filter(doc_d=request.user.provider)[1:]
    elif request.user.provider.Provider_type == 3:
        q = Patient.objects.filter(doc_c=request.user.provider)[1:]
    if request.method =='POST':
        form = PostQform(request.POST)
        if form.is_valid():
            save = PostQ()
            save.Thereciever = (q[0].user)
            save.TheActualsender = (request.user.provider.user)
            save.Thesender = (request.user.provider.user)
            save.Message = form.cleaned_data.get('Message')
            save.save()
            form = PostQform()

            if len(q) >= 1:
                x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
                return render(request, 'blogsys/patient2.html', {"form": form, 'PostQ': x, "q": q[0]})
            else:
                return render(request, 'blogsys/noassigned.html')
        else:
            return HttpResponseBadRequest()
    else:
        form = PostQform()
        if len(q) >= 1:
            x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
            return render(request, 'blogsys/patient2.html', {"form": form, 'PostQ': x, "q": q[0]})
        else:
            return render(request, 'blogsys/noassigned.html')


def Patient3(request):
    if request.user.provider.Provider_type == 1:
        q = Patient.objects.filter(doc_p=request.user.provider)[2:]
    elif request.user.provider.Provider_type == 2:
        q = Patient.objects.filter(doc_d=request.user.provider)[2:]
    elif request.user.provider.Provider_type == 3:
        q = Patient.objects.filter(doc_c=request.user.provider)[2:]
    if request.method =='POST':
        form = PostQform(request.POST)
        if form.is_valid():
            save = PostQ()
            save.Thereciever = (q[0].user)
            save.TheActualsender = (request.user.provider.user)
            save.Thesender = (request.user.provider.user)
            save.Message = form.cleaned_data.get('Message')
            save.save()
            form = PostQform()

            if len(q) >= 1:
                x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
                return render(request, 'blogsys/patient3.html', {"form": form, 'PostQ': x, "q": q[0]})
            else:
                return render(request, 'blogsys/noassigned.html')
        else:
            return HttpResponseBadRequest()
    else:
        form = PostQform()
        if len(q) >= 1:
            x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
            return render(request, 'blogsys/patient3.html', {"form": form, 'PostQ': x, "q": q[0]})
        else:
            return render(request, 'blogsys/noassigned.html')

def Patient4(request):
    if request.user.provider.Provider_type == 1:
        q = Patient.objects.filter(doc_p=request.user.provider)[3:]
    elif request.user.provider.Provider_type == 2:
        q = Patient.objects.filter(doc_d=request.user.provider)[3:]
    elif request.user.provider.Provider_type == 3:
        q = Patient.objects.filter(doc_c=request.user.provider)[3:]
    if request.method =='POST':
        form = PostQform(request.POST)
        if form.is_valid():
            save = PostQ()
            save.Thereciever = (q[0].user)
            save.TheActualsender = (request.user.provider.user)
            save.Thesender = (request.user.provider.user)
            save.Message = form.cleaned_data.get('Message')
            save.save()
            form = PostQform()

            if len(q) >= 1:
                x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
                return render(request, 'blogsys/patient4.html', {"form": form, 'PostQ': x, "q": q[0]})
            else:
                return render(request, 'blogsys/noassigned.html')
        else:
            return HttpResponseBadRequest()
    else:
        form = PostQform()
        if len(q) >= 1:
            x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
            return render(request, 'blogsys/patient4.html', {"form": form, 'PostQ': x, "q": q[0]})
        else:
            return render(request, 'blogsys/noassigned.html')
def Patient5(request):
    if request.user.provider.Provider_type == 1:
        q = Patient.objects.filter(doc_p=request.user.provider)[4:]
    elif request.user.provider.Provider_type == 2:
        q = Patient.objects.filter(doc_d=request.user.provider)[4:]
    elif request.user.provider.Provider_type == 3:
        q = Patient.objects.filter(doc_c=request.user.provider)[4:]
    if request.method =='POST':
        form = PostQform(request.POST)
        if form.is_valid():
            save = PostQ()
            save.Thereciever = (q[0].user)
            save.TheActualsender = (request.user.provider.user)
            save.Thesender = (request.user.provider.user)
            save.Message = form.cleaned_data.get('Message')
            save.save()
            form = PostQform()

            if len(q) >= 1:
                x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
                return render(request, 'blogsys/patient5.html', {"form": form, 'PostQ': x, "q": q[0]})
            else:
                return render(request, 'blogsys/noassigned.html')
        else:
            return HttpResponseBadRequest()
    else:
        form = PostQform()
        if len(q) >= 1:
            x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
            return render(request, 'blogsys/patient5.html', {"form": form, 'PostQ': x, "q": q[0]})
        else:
            return render(request, 'blogsys/noassigned.html')

def Patient6(request):
    if request.user.provider.Provider_type == 1:
        q = Patient.objects.filter(doc_p=request.user.provider)[5:]
    elif request.user.provider.Provider_type == 2:
        q = Patient.objects.filter(doc_d=request.user.provider)[5:]
    elif request.user.provider.Provider_type == 3:
        q = Patient.objects.filter(doc_c=request.user.provider)[5:]
    if request.method =='POST':
        form = PostQform(request.POST)
        if form.is_valid():
            save = PostQ()
            save.Thereciever = (q[0].user)
            save.TheActualsender = (request.user.provider.user)
            save.Thesender = (request.user.provider.user)
            save.Message = form.cleaned_data.get('Message')
            save.save()
            form = PostQform()

            if len(q) >= 1:
                x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
                return render(request, 'blogsys/patient6.html', {"form": form, 'PostQ': x, "q": q[0]})
            else:
                return render(request, 'blogsys/noassigned.html')
        else:
            return HttpResponseBadRequest()
    else:
        form = PostQform()
        if len(q) >= 1:
            x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
            return render(request, 'blogsys/patient6.html', {"form": form, 'PostQ': x, "q": q[0]})
        else:
            return render(request, 'blogsys/noassigned.html')

def Patient7(request):
    if request.user.provider.Provider_type == 1:
        q = Patient.objects.filter(doc_p=request.user.provider)[6:]
    elif request.user.provider.Provider_type == 2:
        q = Patient.objects.filter(doc_d=request.user.provider)[6:]
    elif request.user.provider.Provider_type == 3:
        q = Patient.objects.filter(doc_c=request.user.provider)[6:]
    if request.method =='POST':
        form = PostQform(request.POST)
        if form.is_valid():
            save = PostQ()
            save.Thereciever = (q[0].user)
            save.TheActualsender = (request.user.provider.user)
            save.Thesender = (request.user.provider.user)
            save.Message = form.cleaned_data.get('Message')
            save.save()
            form = PostQform()

            if len(q) >= 1:
                x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
                return render(request, 'blogsys/patient7.html', {"form": form, 'PostQ': x, "q": q[0]})
            else:
                return render(request, 'blogsys/noassigned.html')
        else:
            return HttpResponseBadRequest()
    else:
        form = PostQform()
        if len(q) >= 1:
            x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
            return render(request, 'blogsys/patient7.html', {"form": form, 'PostQ': x, "q": q[0]})
        else:
            return render(request, 'blogsys/noassigned.html')

def Patient8(request):
    if request.user.provider.Provider_type == 1:
        q = Patient.objects.filter(doc_p=request.user.provider)[7:]
    elif request.user.provider.Provider_type == 2:
        q = Patient.objects.filter(doc_d=request.user.provider)[7:]
    elif request.user.provider.Provider_type == 3:
        q = Patient.objects.filter(doc_c=request.user.provider)[7:]
    if request.method =='POST':
        form = PostQform(request.POST)
        if form.is_valid():
            save = PostQ()
            save.Thereciever = (q[0].user)
            save.TheActualsender = (request.user.provider.user)
            save.Thesender = (request.user.provider.user)
            save.Message = form.cleaned_data.get('Message')
            save.save()
            form = PostQform()

            if len(q) >= 1:
                x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
                return render(request, 'blogsys/patient8.html', {"form": form, 'PostQ': x, "q": q[0]})
            else:
                return render(request, 'blogsys/noassigned.html')
        else:
            return HttpResponseBadRequest()
    else:
        form = PostQform()
        if len(q) >= 1:
            x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
            return render(request, 'blogsys/patient8.html', {"form": form, 'PostQ': x, "q": q[0]})
        else:
            return render(request, 'blogsys/noassigned.html')

def Patient9(request):
    if request.user.provider.Provider_type == 1:
        q = Patient.objects.filter(doc_p=request.user.provider)[8:]
    elif request.user.provider.Provider_type == 2:
        q = Patient.objects.filter(doc_d=request.user.provider)[8:]
    elif request.user.provider.Provider_type == 3:
        q = Patient.objects.filter(doc_c=request.user.provider)[8:]
    if request.method =='POST':
        form = PostQform(request.POST)
        if form.is_valid():
            save = PostQ()
            save.TheActualsender = (request.user.provider.user)
            save.Thereciever = (q[0].user)
            save.Thesender = (request.user.provider.user)
            save.Message = form.cleaned_data.get('Message')
            save.save()
            form = PostQform()

            if len(q) >= 1:
                x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
                return render(request, 'blogsys/patient9.html', {"form": form, 'PostQ': x, "q": q[0]})
            else:
                return render(request, 'blogsys/noassigned.html')
        else:
            return HttpResponseBadRequest()
    else:
        form = PostQform()
        if len(q) >= 1:
            x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
            return render(request, 'blogsys/patient9.html', {"form": form, 'PostQ': x, "q": q[0]})
        else:
            return render(request, 'blogsys/noassigned.html')

def Patient10(request):
    if request.user.provider.Provider_type == 1:
        q = Patient.objects.filter(doc_p=request.user.provider)[9:]
    elif request.user.provider.Provider_type == 2:
        q = Patient.objects.filter(doc_d=request.user.provider)[9:]
    elif request.user.provider.Provider_type == 3:
        q = Patient.objects.filter(doc_c=request.user.provider)[9:]
    if request.method =='POST':
        form = PostQform(request.POST)
        if form.is_valid():
            save = PostQ()
            save.TheActualsender = (request.user.provider.user)
            save.Thereciever = (q[0].user)
            save.Thesender = (request.user.provider.user)
            save.Message = form.cleaned_data.get('Message')
            save.save()
            form = PostQform()
            if len(q) >= 1:
                x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
                return render(request, 'blogsys/patient10.html', {"form": form, 'PostQ': x, "q": q[0]})
            else:
                return render(request, 'blogsys/noassigned.html')
        else:
            return HttpResponseBadRequest()
    else:
        form = PostQform()
        if len(q) >= 1:
            x = PostQ.objects.filter(Thesender=(request.user.provider.user), Thereciever=(q[0].user))
            return render(request, 'blogsys/patient10.html', {"form": form, 'PostQ': x, "q": q[0]})
        else:
            return render(request, 'blogsys/noassigned.html')

def noassigned(request):
    return render(request, 'blogsys/noassigned.html')

