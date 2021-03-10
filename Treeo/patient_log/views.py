from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from patient_log.models import PatientLog
from .forms import PatientLogForm, AdminProviderLogForm
from decimal import Decimal
from django.contrib import messages
from django.views.generic import TemplateView
from chartjs.views.lines import BaseLineChartView
from patient_log.models import PatientLog
from django.db.models import Sum
from django.contrib.auth.decorators import login_required, user_passes_test
import sched, time
from django.views.generic.edit import UpdateView
import datetime
from django.db.models import Q

@login_required
def patientlog(request):
    if request.method =='POST':
        if request.user.user_type==3:
            form = PatientLogForm(request.POST)
            if form.is_valid():
                saverecord = PatientLog()
                saverecord.patient = request.user.patient
                saverecord.calories = form.cleaned_data.get('calories')
                saverecord.water = form.cleaned_data.get('water')
                saverecord.mood = form.cleaned_data.get('mood')
                saverecord.sleep = form.cleaned_data.get('sleep')
                saverecord.save()
                return render(request, 'patient_log/patientLog_submit.html', {"form": saverecord})
            else:
                return render(request, 'patient_log/patientLog.html', {"form": PatientLogForm(),'formerrors': form})
        elif request.user.user_type==2:
            return redirect('log-chart', request.POST['patient'])
        elif request.user.user_type == 1:
            return redirect('log-chart', request.POST['patient'])
    else:
        if request.user.user_type==3:
            today = datetime.datetime.today().date()
            if PatientLog.objects.filter(patient=request.user.patient.id).filter(date__date=today).exists():
                saverecord = PatientLog.objects.get(Q(patient=request.user.patient.id) & Q(date__date=today))
                return redirect('edit_log',saverecord.id)
            else:
                #link to chart on the page
                return render(request, 'patient_log/patientLog.html', {"form": PatientLogForm()})
        elif request.user.user_type==2:
            return render(request, 'patient_log/patientLog.html', {"form": AdminProviderLogForm(instance=request)})
        elif request.user.user_type == 1:
            #reject admins
            return render(request, 'patient_log/patientLog.html', {"form": AdminProviderLogForm(instance=request)})

def edit_log(request,id):
    temp = PatientLog.objects.get(id=id)
    form = PatientLogForm()
    if request.method =='POST':
        print("test")
        form = PatientLogForm(request.POST)
        if form.is_valid():
            temp.calories = form.cleaned_data.get('calories')
            temp.water = form.cleaned_data.get('water')
            temp.mood = form.cleaned_data.get('mood')
            temp.sleep = form.cleaned_data.get('sleep')
            temp.save()
            #message.success(request,'')
            #redirects to self
            return render(request, 'patient_log/patientLog_submit.html')
        else:
            form2=PatientLogForm()
        return render(request,'patient_log/editLog.html', {'edit_log': form2,'formerrors': form, 'form':temp})
    else:
        return render(request, 'patient_log/editLog.html', {'edit_log': form, 'form': temp})

def line_chart_Year(request,id):
    labels = ["January", "February", "March", "April", "May", "June", "July","August", "September", "October", "November", "December"]
    data = []
    data2 = []
    data3 = []
    data4 = []
    #for current year loop through the months and append the average to list make 0 jan 2 feb ect
    cur_date = datetime.datetime.today()

    #second for loop for the years in the PatientLog
    for i in range(1, 13):
        temp = list(PatientLog.objects.filter(patient=id).filter(date__year=cur_date.year).filter(date__month=i).aggregate(Sum('calories')).values())
        if None not in temp:
            temp[0] = float(temp[0])
            data += temp
        else:
            data += ['NaN']
        temp = list(PatientLog.objects.filter(patient=id).filter(date__year=cur_date.year).filter(date__month=i).aggregate(Sum('water')).values())
        if None not in temp:
            temp[0] = float(temp[0])
            data2 += temp
        else:
            data2 += ['NaN']
        temp = list(PatientLog.objects.filter(patient=id).filter(date__year=cur_date.year).filter(date__month=i).aggregate(Sum('sleep')).values())
        if None not in temp:
            temp[0] = float(temp[0])
            data3 += temp
        else:
            data3 += ['NaN']
        temp = list(PatientLog.objects.filter(patient=id).filter(date__year=cur_date.year).filter(date__month=i).aggregate(Sum('mood')).values())
        if None not in temp:
            temp[0] = float(temp[0])
            data4 += temp
        else:
            data4 += ['NaN']
    # for i,val in enumerate(data):
    #     if data[i] != 'NaN':
    #         data[i] = float(val)
    # for i,val in enumerate(data2):
    #     if data2[i] != 'NaN':
    #         data2[i] = float(val)
    # for i,val in enumerate(data3):
    #     if data3[i] != 'NaN':
    #         data3[i] = float(val)
    # for i,val in enumerate(data4):
    #     if data4[i] != 'NaN':
    #         data4[i] = float(val)
    print(data, data2, data3, data4)
    return render(request, 'patient_log/chart_View.html', {
        'labels': labels,
        'data': data,
        'data2': data2,
        'data3': data3,
        'data4': data4,
    })

def line_chart_Week(request,id):
    labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    data = []
    data2 = []
    data3 = []
    data4 = []
    #for current week
    cur_date = datetime.datetime.today()
    weekday = cur_date.weekday()
    dates = []
    date = cur_date - datetime.timedelta(days=weekday)
    for i in range(7):
        dates.append(date + datetime.timedelta(days=i))
    for i in dates:
        temp = list(PatientLog.objects.filter(patient=id).filter(date__date=i).aggregate(Sum('calories')).values())
        if None not in temp:
            temp[0] = float(temp[0])
            data += temp
        else:
            data += ['NaN']
        temp = list(PatientLog.objects.filter(patient=id).filter(date__date=i).aggregate(Sum('water')).values())
        if None not in temp:
            temp[0] = float(temp[0])
            data2 += temp
        else:
            data2 += ['NaN']
        temp = list(PatientLog.objects.filter(patient=id).filter(date__date=i).aggregate(Sum('sleep')).values())
        if None not in temp:
            temp[0] = float(temp[0])
            data3 += temp
        else:
            data3 += ['NaN']
        temp = list(PatientLog.objects.filter(patient=id).filter(date__date=i).aggregate(Sum('mood')).values())
        if None not in temp:
            temp[0]=float(temp[0])
            data4 += temp
        else:
            data4 += ['NaN']
    print(data,data2,data3,data4)
    # for i,val in enumerate(data):
    #     if data[i] != 'NaN':
    #         data[i] = float(val)
    # for i,val in enumerate(data2):
    #     if data2[i] != 'NaN':
    #         data2[i] = float(val)
    # for i,val in enumerate(data3):
    #     if data3[i] != 'NaN':
    #         data3[i] = float(val)
    # for i,val in enumerate(data4):
    #     if data4[i] != 'NaN':
    #         data4[i] = float(val)
    print(data, data2, data3, data4)
    return render(request, 'patient_log/chart_View.html', {
        'labels': labels,
        'data': data,
        'data2': data2,
        'data3': data3,
        'data4': data4,
    })

# def chart(request):
#     return render(request,'patient_log/chart_View.html')
#
# class Circle(BaseLineChartView):
#     slug = None
#     print("2")
#     def get_labels(self):
#         return ["January", "February", "March", "April", "May", "June", "July","August", "September", "October", "November", "December"]
#
#     def get_providers(self):
#         return ["Central", "Eastside", "Westside"]
#
#
#     def get_data(self):
#         aaa = list(PatientLog.objects.filter(patient=id).aggregate(Sum('blood')).values())[0]
#         baa = list(PatientLog.objects.filter(patient=id).aggregate(Sum('calories')).values())[0]
#         caa = list(PatientLog.objects.filter(patient=id).aggregate(Sum('water')).values())[0]
#         print(self.kwargs['slug'])
#         return [[ baa, 2000,1222,1111],
#               [aaa, 2.1],
#                 [caa,1.4]]










