"""Treeo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('apptArchive/', include('apptArchive.urls')),
    path('admin/', admin.site.urls),
    path('ReqAppt/', include('ReqAppt.urls')),
    path('upload_download/', include('upload_download.urls')),
    path('', include('users_acc.urls')),
    path('patient_log/', include('patient_log.urls')),
    path('blogsys/', include('blogsys.urls')),
    path('messaging/', include('messaging.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) is for debug only for prodution consult documentation for deploying static files