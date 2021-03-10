import time
import datetime
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.contrib import auth
from django.contrib import messages

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object




class SessionTimeoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # is there a signed in user and does this request have a session atribute
        if not hasattr(request, "session") or request.user.is_authenticated:
            return
        #get this time if not set use now time as default
        Initial_time = request.session.setdefault("Initial_time", time.time())
        timelimit = getattr(settings, "SESSION_COOKIE_AGE", 300)
        # print(Initial_time,timelimit)
        #if the current time minus the initial is more than the timelimit then redirect to login with forewarding and logout
        if (time.time() - Initial_time) > timelimit:
            auth.logout(request)
            #add message about time out to the redirect
            messages.error(request, "Session Timed Out.")
            return redirect_to_login(next=request.path)
        request.session["Initial_time"] = time.time()
        # print(request.session["Initial_time"])