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
from django.urls import path
from . import views

urlpatterns = [
    #path('', views.render_file_upload),
    path('upload/', views.render_file_upload, name='upload_download_file_upload'),
    path('download/', views.render_file_download, name='upload_download_file_download'),
    path('file_upload_Complete/', views.render_file_upload, name='upload_download_file_upload_Complete'),
    path('file_upload_Failed/', views.render_file_upload, name='upload_download_file_upload_Failed'),
    path('delete/<id>', views.delete_file, name='upload_download_file_delete'),
]
