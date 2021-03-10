import calendar
import json

from django.contrib.sites import requests
import math

from utils.calendar import Calendar
from django.utils.safestring import mark_safe
from ReqAppt import models
from datetime import datetime, date, timedelta
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse, HttpResponseRedirect
from ReqAppt import models
from ReqAppt.forms import *
from ReqAppt.models import ApptTable
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from .sms import *
from .email import *
from datetime import datetime
import requests
from apptArchive.models import ApptArchive


User = get_user_model()

def base64_encode(message):
    import base64
    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode('ascii')
    return base64_message



def reqAppt_calendar(request):
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     d = get_date(self.request.GET.get('month', None))
    #     cal = Calendar(d.year, d.month)

    def previous_month(dday):
        firstDayofMonth = dday.replace(day=1)
        previous_month = firstDayofMonth - timedelta(days=1)
        calMonth = 'month=' + str(previous_month.year) + '-' + str(previous_month.month)
        return calMonth

    def next_month(dday):
        days_in_month = calendar.monthrange(dday.year, dday.month)[1]
        last = dday.replace(day=days_in_month)
        next_month = last + timedelta(days=1)
        month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
        return month


    #placeholder for a year and a month
    if 'month' in request.GET:
        year, month = request.GET['month'].split("-")
        year, month = int(year), int(month)
        dday = date(year=year, month=month, day=1)
    else:
        dday = datetime.now()

    cal = Calendar(dday.year, dday.month, request)
    html_cal = cal.formatTheMonth(withyear=True)
    context = {}
    context['calendar'] = mark_safe(html_cal)
    context['prev_month'] = previous_month(dday)
    context['next_month'] = next_month(dday)
    return render(request,'ReqAppt/apt_calendar.html', context)

@login_required
def home(request):
    if request.user.user_type==1:
        return Admin_view(request)
    elif request.user.user_type == 2:
        return Doctor_view(request)
    elif request.user.user_type == 3:
        return Patient_view(request)
    else:
        return render(request,'ReqAppt/apt_home.html')

def Pending(request):
    return render(request,'ReqAppt/Pending.html')


def create_Appointment(request):
    if request.method == 'POST':
        form = ApptRequestFormPatient(data=request.POST, instance=request.user)
        if not form.is_valid():
            form2 = ApptRequestFormPatient(instance=request.user)
            return render(request, 'ReqAppt/appointment.html', {"form": form2,'formerrors': form})
            #return HttpResponseBadRequest()
        else:

            # Valid, persist in db
            print(request.POST)
            apptDate = request.POST['apptDate']
            apptHour = float(request.POST['apptHour'])
            print(apptDate)
            print(apptHour)
            meetingDate = datetime.strptime(apptDate, "%m/%d/%Y")
            hour = int(math.floor(apptHour))
            minute = int((apptHour - hour) * 60)
            meetingDate = meetingDate.replace(hour=hour, minute=minute)
            print(meetingDate)
            #call zoom api make meeting and get the url for it
            # ApptTable.objects.create(
            #     **form.cleaned_data, meetingDate=meetingDate meeturl=zoom url
            # )
            appointment=ApptTable.objects.create(
                **form.cleaned_data, meetingDate=meetingDate
            )

            # Oath, TODO use JWT if this doesn't work
            scheduled_mail_both(appointment)
            target_time_print(appointment)
            send_message(appointment)
            return render(request, 'ReqAppt/Pending.html')


    else:
        form = ApptRequestFormPatient(instance=request.user)
        return render(request,'ReqAppt/appointment.html', {"form": form})
        #provider = form.cleaned_data.get('user_defined_code')


def Doctor_view(request):
    x = ApptTable.objects.filter(provider= request.user.provider.id).order_by('meetingDate')
    return render(request,'ReqAppt/Doctor_view.html',{'ApptTable':x})


def Admin_view(request):
    #need to make some search criteria here
    x = ApptTable.objects.all()
    return render(request, 'ReqAppt/Admin_view.html', {'ApptTable': x})


def Patient_view(request):
    x = ApptTable.objects.filter(patient=request.user.patient.id).order_by('meetingDate')
    for i in x:
        print(i.meetingDate)
    return render(request,'ReqAppt/Patient_view.html',{'ApptTable':x})

def approve(request,id):
    appointment=ApptTable.objects.get(apptId=id)
    appointment.status=True
    appointment.save()
    approve_message(appointment)
    approved_mail_both(appointment)
    return redirect("reqAppt_Doctor")

def Destroy(request, id):
    appointment = ApptTable.objects.get(apptId=id)
    if request.method == 'POST':
        appointment.delete()
        reject_message(appointment)
        delete_mail_both(appointment)
        return redirect ("reqAppt_Doctor")
    return render(request,"reqAppt/DeleteConfirm.html")

STARTING_HOUR = 8
ENDING_HOUR = 16
def Doctor_avail_view(request, id, date_str):
    # parse datetime
    # query appointments for id(provider) on date
    # filter for available hour slots from 8-4 , return json list
    month, day, year = date_str.split('-')
    appointments = ApptTable.objects.filter(
        provider_id=id,
        meetingDate__year=str(year),
        meetingDate__month=str(month),
        meetingDate__day=str(day),
    ).all()

    def appt_to_time(appt: ApptTable):
        return appt.meetingDate.hour + (appt.meetingDate.minute * 0.5)

    unavailable_times = {appt_to_time(appt) for appt in appointments}

    # data = [h/2 for h in range(STARTING_HOUR * 2, (ENDING_HOUR + 1) * 2) if h/2 not in unavailable_times]
    data = [h for h in range(STARTING_HOUR , ENDING_HOUR + 1) if h not in unavailable_times]

    return JsonResponse(data, safe=False)


#### FULL CALL
def event(request):
    meeting_arr = []
    #if request.GET.get('patient') == "all":
    #    all_meetings = ApptTable.objects.all()
    #else:
    #    all_meetings = ApptTable.objects.filter(event_type__icontains=request.GET.get('event_type'))

    is_patient = [type_name for t, type_name in USER_TYPE_CHOICES if t == request.user.user_type][0] == 'Patient'
    if is_patient:
        all_meetings = ApptTable.objects.filter(patient__user_id=request.user.id).all()
    else:
        all_meetings = ApptTable.objects.filter(provider__user_id=request.user.id).all()

    for i in all_meetings:
        meeting_sub_arr = {}
        user = (i.provider if is_patient else i.patient).user
        meeting_sub_arr['title'] = f"{user.first_name} {user.last_name}"
        start = i.meetingDate.strftime('%Y-%m-%dT%H:%M:%S')
        end = (i.meetingDate + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
        #meetingDate = datetime.strptime(str(i.meetingDate.date()), "%Y-%m-%d").strftime("%Y-%m-%d")
        meeting_sub_arr['start'] = start
        meeting_sub_arr['end'] = end
        meeting_arr.append(meeting_sub_arr)
    return HttpResponse(json.dumps(meeting_arr))

def fullcalendar(request):
    all_meetings = ApptTable.objects.all()
    get_meeting_patients = ApptTable.objects.only('patient')

    # if filters applied then get parameter and filter based on condition else return object
    print(request.method)

    context = {
        "meeting":all_meetings,
        "get_meeting_patient":get_meeting_patients,
    }
    return render(request,'ReqAppt/fullcalendar.html',context)

def archive_apt(request,id):
    appointment = ApptTable.objects.get(apptId=id)
    try:
        archiveAppt = ApptArchive.objects.create()
        archiveAppt.meetingDate = appointment.meetingDate
        archiveAppt.provider = appointment.provider
        archiveAppt.patient = appointment.patient
        archiveAppt.save()
        appointment.delete()
        return render(request,"reqAppt/appointment.html")
    except Exception as e:
        print(e)
        return render(request,"reqAppt/appointment.html")
#
# def zoom_callback(request):
#     code = request.GET["code"]
#     data = requests.post(f"https://zoom.us/oauth/token?grant_type=authorization_code&code="
#                          f"obBEe8ewaL_KdYKjnimT4KPd8KKdQt9FQ&redirect_uri="
#                          f"http://127.0.0.1:8000/ReqAppt/Appointment", headers={
#         "Authorization": "Basic " + base64_encode("OoIw_Ll1SPG3Me81tIYqQ:0pbxapRDeB187rtT6SQSztYV9obAQpK6")
#     })
#     print(data.text)
#     requests.session["zoom_access_token"] = data.json()["access_token"]
#
#     return HttpResponseRedirect("/ReqAppt/appointment")
#
#
#
# def schedule_interview(request):
#     if request.method == "POST":
#
#         patient = User.objects.get(id=int(request.POST["patient"]))
#         # patient = Profile.objects.get(patient=patient)
#
#         data = requests.post("https://api.zoom.us/v2/users/me/meetings", headers={
#             'content-type': "application/json",
#             "authorization": f"Bearer {request.session['zoom_access_token']}"
#         }, data=json.dumps({
#             "topic": f"Interview with {ApptTable.patient.name}",
#             "type": 2,
#             "start_time": request.POST["time"],
#         }))
#
#         print("*)(@*$)@($*)@($*@)(#*@#)(*@#")
#         print(data.json()["join_url"], data.json()["start_url"])
#
#         return HttpResponseRedirect(f"/ReqAppt/Appointment")
#

    is_patient = [type_name for t, type_name in USER_TYPE_CHOICES if t == request.user.user_type][0] == 'Patient'
    if is_patient:
        all_meetings = ApptTable.objects.filter(patient__user_id=request.user.id).all()
    else:
        all_meetings = ApptTable.objects.filter(provider__user_id=request.user.id).all()

    for i in all_meetings:
        meeting_sub_arr = {}
        user = (i.provider if is_patient else i.patient).user
        meeting_sub_arr['title'] = f"{user.first_name} {user.last_name}"
        start = i.meetingDate.strftime('%Y-%m-%dT%H:%M:%S')
        end = (i.meetingDate + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
        #meetingDate = datetime.strptime(str(i.meetingDate.date()), "%Y-%m-%d").strftime("%Y-%m-%d")
        meeting_sub_arr['start'] = start
        meeting_sub_arr['end'] = end
        meeting_arr.append(meeting_sub_arr)
    return HttpResponse(json.dumps(meeting_arr))

def fullcalendar(request):
    all_meetings = ApptTable.objects.all()
    get_meeting_patients = ApptTable.objects.only('patient')

    # if filters applied then get parameter and filter based on condition else return object
    print(request.method)

    context = {
        "meeting":all_meetings,
        "get_meeting_patient":get_meeting_patients,
    }
    return render(request,'ReqAppt/fullcalendar.html',context)

def archive_apt(request,id):
    appointment = ApptTable.objects.get(apptId=id)
    try:
        archiveAppt = ApptArchive.objects.create()
        archiveAppt.meetingDate = appointment.meetingDate
        archiveAppt.provider = appointment.provider
        archiveAppt.patient = appointment.patient
        archiveAppt.save()
        appointment.delete()
        return redirect('apptArchive')
    except Exception as e:
        print(e)
        return render(request,"reqAppt/appointment.html")
#
# def zoom_callback(request):
#     code = request.GET["code"]
#     data = requests.post(f"https://zoom.us/oauth/token?grant_type=authorization_code&code="
#                          f"obBEe8ewaL_KdYKjnimT4KPd8KKdQt9FQ&redirect_uri="
#                          f"http://127.0.0.1:8000/ReqAppt/Appointment", headers={
#         "Authorization": "Basic " + base64_encode("OoIw_Ll1SPG3Me81tIYqQ:0pbxapRDeB187rtT6SQSztYV9obAQpK6")
#     })
#     print(data.text)
#     requests.session["zoom_access_token"] = data.json()["access_token"]
#
#     return HttpResponseRedirect("/ReqAppt/appointment")
#
#
#
# def schedule_interview(request):
#     if request.method == "POST":
#
#         patient = User.objects.get(id=int(request.POST["patient"]))
#         # patient = Profile.objects.get(patient=patient)
#
#         data = requests.post("https://api.zoom.us/v2/users/me/meetings", headers={
#             'content-type': "application/json",
#             "authorization": f"Bearer {request.session['zoom_access_token']}"
#         }, data=json.dumps({
#             "topic": f"Interview with {ApptTable.patient.name}",
#             "type": 2,
#             "start_time": request.POST["time"],
#         }))
#
#         print("*)(@*$)@($*)@($*@)(#*@#)(*@#")
#         print(data.json()["join_url"], data.json()["start_url"])
#
#         return HttpResponseRedirect(f"/ReqAppt/Appointment")
#



