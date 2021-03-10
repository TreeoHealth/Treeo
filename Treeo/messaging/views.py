from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db import models
from django.contrib.auth.decorators import login_required
from . import forms
from .models import *
from users_acc.models import *

@login_required()
def test(request):
    context={}
    master_list = []
    message_list=[]
    if request.user.user_type == 1:
        conversation_list = User.objects.filter(sender__reciever=request.user).distinct()
        for i in conversation_list:
            message_list = message.objects.filter(reciever=request.user, sender=i).order_by('send_time')
            master_list.append(message_list)
        print(master_list)
    elif request.user.user_type == 2:
        current_conversation_people = User.objects.filter(sender__reciever=request.user).distinct()
        if request.user.provider.Provider_type == 1:
            patient_list = Patient.objects.filter(doc_p=request.user.provider)
        elif request.user.provider.Provider_type == 2:
            patient_list = Patient.objects.filter(doc_d=request.user.provider)
        elif request.user.provider.Provider_type == 3:
            patient_list = Patient.objects.filter(doc_c=request.user.provider)
        if not patient_list:
            for i in patient_list:
                message_list = message.objects.filter(reciever=request.user, sender=i.user).order_by('send_time')
                if not message_list:
                    #no messages for that patient
                    master_list.append(message_list)
        else:
            pass
            #something for no patients or handle in templates
        print(master_list)
    elif request.user.user_type == 3:
        current_conversation_people = User.objects.filter(sender__reciever=request.user).distinct()
        try:
            if request.user.patient.doc_c.user is not None:
                if request.user.patient.doc_c.user in current_conversation_people:
                    print("TEST Doc C")
                message_list=message.objects.filter(reciever=request.user, sender=request.user.patient.doc_c.user).order_by('send_time')
                master_list.append(message_list)
        except:
            pass
        try:
            if request.user.patient.doc_d.user is not None:
                if request.user.patient.doc_d.user in current_conversation_people:
                    print("TEST Doc D")
                message_list=message.objects.filter(reciever=request.user, sender=request.user.patient.doc_d.user).order_by('send_time')
                master_list.append(message_list)
        except:
            pass
        try:
            if request.user.patient.doc_p.user is not None:
                if request.user.patient.doc_p.user in current_conversation_people:
                    print("TEST Doc P")
                message_list=message.objects.filter(reciever=request.user, sender=request.user.patient.doc_p.user).order_by('send_time')
                master_list.append(message_list)
        except:
            pass
        conversation_list = User.objects.filter(sender__reciever=request.user).distinct()
        for i in conversation_list:
            message_list = message.objects.filter(reciever=request.user, sender=i).order_by('send_time')
            master_list.append(message_list)
        print(master_list)
        # doesnt handle former patients
        #master list is a list of all the conversations ie a set(stored as a list) of lists with each list in the set having of all of the messages
        # from one other user to the current logged in user
        #how do we handle empty messages since we can derive user data from already sent messages  but if there are no messages between 2 users we cant start a conversation
        #options start each user off with a default welcome message when the docs are assigned a patient and when a care team is assigned to a patient?
        #or we can send tuples with the user and messages(user,messages) with some having [] messages
        #both add some data overhead but i think that the tuples are a solid way to go as they dont add to database size but add to execution load
        #could also be mitigated with a list of stored converation threads where we get those check if any
        # new patients are assigned and add new ones doesnt cover threads made by mistake this is not an expected use case but still
    context['message_data'] = master_list

    #do in html???
    # list_of_recipients=[]
    # for i in conversation_list:
    #     if i.user_type ==2:
    #         name=request.user.provider.get_Provider_type_display()+" "+request.user.first_name+" "+request.user.last_name
    #         list_of_recipients.append(name)
    #         print(name)
    #     elif i.user_type ==3:
    #         name=request.user.first_name+" "+request.user.last_name
    #         list_of_recipients.append(name)
    #         print(name)
    #     elif i.user_type == 1:
    #         #add title to admin model?
    #         name = "Administator "+request.user.first_name + " " + request.user.last_name
    #         list_of_recipients.append(name)
    #         print(name)
    # print(list_of_recipients)
    return render(request, 'messaging/index.html',context)
@login_required
def inbox(request):
    # favorites = message.objects.filter(reciever=request.user)#.values('sender').distinct()
    # color_ids = favorites .values_list('sender', flat=True).distinct()
    # colors = User.objects.filter(id__in=color_ids)
    conversation_list=User.objects.filter(sender__reciever=request.user).distinct()
    message_list=[]
    #do in html???
    list_of_recipients=[]
    for i in conversation_list:
        if i.user_type ==2:
            name=request.user.provider.get_Provider_type_display()+" "+request.user.first_name+" "+request.user.last_name
            list_of_recipients.append(name)
            print(name)
        elif i.user_type ==3:
            name=request.user.first_name+" "+request.user.last_name
            list_of_recipients.append(name)
            print(name)
        elif i.user_type == 1:
            #add title to admin model?
            name = "Administator "+request.user.first_name + " " + request.user.last_name
            list_of_recipients.append(name)
            print(name)
    print(list_of_recipients)

    #this should return list of converastion and then render the one that is clicked on
    return render(request, 'messaging/inbox.html', {'message_list': message_list})





















#
# #add chices {for }
# #folder= folder the user is looking at default inbox not neeeded as its a conversation thing???
# #all messages that the user recieved that aren't perminitly deleted and that arte in the current folder
# #mabye make a list of all of the messages that the user recieved that aren't perminitly deleted = john
# # and then querry john for everything that is for the folder?????
# #folder=message.objects.filter(reciever = request.user).filter(perm_del = 0).filter(reciever_loc = "folder")
#
# @login_required
# def inbox(request):
#     message_list = message.objects.filter(reciever=request.user).order_by('send_time')
#     #this should return list of converastion and then render the one that is clicked on
#     return render(request, 'messaging/inbox.html', {'message_list': message_list})
#
# @login_required
# def render_conversation(request, convo_id):
#     message_list = message.objects.filter(reciever=request.user, convoID=convo_id).order_by('send_time')
#     if message_list:
#         for i in message_list:
#             i.read_status=1
#             i.save()
#     #change all messages in convo to read
#     return render(request, 'messaging/inbox.html', {'message_list': message_list})
#
# @login_required
# def list_conversation_active(request):
#     message_list = message.objects.filter(reciever=request.user,perm_del=False).values_list('convoID').distinct()
#     if message_list:
#         for i in message_list:
#             #order by read and see if firset
#             message_list = message.objects.filter(reciever=request.user, perm_del=False, convoID=i[0]).order_by('send_time').first()
#             print(message_list)
#     # print(convo id,reciever,sender ,if unread messages, subject????)
#         #does this need to return or just
#     return render(request, 'messaging/inbox.html', {'message_list': message_list})
#
#
# @login_required
# def list_conversation_deleted(request):
#     #true if one deleted method???????????
#     message_list = message.objects.filter(reciever=request.user,perm_del=True).values_list('convoID').distinct()
#     if message_list:
#         for i in message_list:
#             message_list = message.objects.filter(reciever=request.user, perm_del=False, convoID=i[0]).order_by('send_time').first()
#             print(message_list)
#     # print(convo id,reciever,sender ,if unread messages)
#         #does this need to return or just
#     return render(request, 'messaging/inbox.html', {'message_list': message_list})
#
#
#
# @login_required
# def delete_conversation(request, convo_id):
#     message_list = message.objects.filter(reciever=request.user,perm_del=False, convoID=convo_id)
#     if message_list:
#         for i in message_list:
#             i.perm_del=1
#             i.save()
#     return redirect('messaging_home')
#
#
# @login_required
# def undelete_conversation(request, convo_id):
#     message_list = message.objects.filter(reciever=request.user,perm_del=True, convoID=convo_id)
#     if message_list:
#         for i in message_list:
#             i.perm_del=0
#             i.save()
#     return redirect('messaging_home')
#
# @login_required
# def delete_message(request, id):
#     message_list = message.objects.filter(id=id)
#     print(message_list)
#     if message_list:
#         for i in message_list:
#             i.perm_del=1
#             i.save()
#             #change to redirect
#             return render_conversation(request, i.convoID)
#     else:
#         return redirect('messaging_home')
#
# @login_required
# def undo_delete(request, id):
#     message_list = message.objects.filter(id=id)
#     if message_list:
#         for i in message_list:
#             print(i.perm_del)
#             i.perm_del=0
#             i.save()
#             return render_conversation(request, i.convoID)
#     else:
#         return redirect('messaging_home')
#
# @login_required
# def unread_count(request):
#     message_list = message.objects.filter(reciever=request.user,perm_del=False, read_status=0)
#     if len(message_list)>0:
#         return len(message_list)
#     else:
#         return 0
#
# @login_required
# def new_convo(request):
#     # use a form with the error checking for proifanity here
#     m = message.objects.create()
#     m.sender = request.user
#     m.reciever = form.stuff
#     m.subject = form.stuff
#     # auto increments so not needed m.convoID = convo_id
#     m.read_status = True
#     m.sender_loc = 'Outbox'
#     m.reciever_loc = 'Inbox'
#     m.save()
#
# @login_required
# def reply(request, ):
#     # use a form with the error checking for proifanity here
#     m = message.objects.create()
#     m.sender = request.user
#     m.reciever = recipient
#     m.subject = form.stuff
#     m.convoID = convo_id
#     m.read_status = True
#     m.sender_loc = 'Outbox'
#     m.reciever_loc = 'Inbox'
#     m.save()
