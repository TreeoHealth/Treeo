from django.db import models
from django.contrib.auth import get_user_model

class message(models.Model):
    #django auto makes a primary key field for id so message.id will get you this
    #ok so this is interesting do the messages have to be scene from the people after the user is deactivated
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='sender', null=True, blank=True)
    reciever = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='reciever', null=True, blank=True)
    subject = models.CharField(max_length = 70)
    msgbody = models.CharField(max_length = 700)
    # this is for the reply chanin thing in email thing????????? make this a auto incrementing field?
    #convoID = models.AutoField()
    convoID = models.CharField(max_length = 30)
    send_time = models.DateTimeField(auto_now_add=True)
    #instead of read status have read time default to nul so if not read then null and if read the delivered or just keep it as binary
    read_status = models.BooleanField(default=False)#1 yes 0 no
    # purpose now????folder that the user has the message in. inbox sent ect
    sender_loc = models.CharField(max_length = 30)
    reciever_loc = models.CharField(max_length = 30)
    # still storeing the mesage in db after the user have deleted it to allow for undelete
    perm_del = models.BooleanField(default=False)#1 yes 0 no
