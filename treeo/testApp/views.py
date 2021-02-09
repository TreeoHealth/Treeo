from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

#like a flask endpoint (function that is called by some action/link in the testApp urls conf file)
def index(request): 
    return HttpResponse("Hello, world. You're at the index.")