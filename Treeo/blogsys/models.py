from django.db import models
from django.contrib.auth import get_user_model

class PostQ(models.Model):
    Thesender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='Thesender', null=True, blank=True)
    TheActualsender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='TheActualsender', null=True,blank=True)
    Thereciever = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='Thereciever', null=True, blank=True)
    Message = models.CharField(max_length=200)
    meetingDate = models.DateTimeField(auto_now_add=True)
