from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from .forms import Fileform
from django.core.files.storage import FileSystemStorage
from .models import Uploaded_File
from django.views.generic.edit import DeleteView
from django.contrib.auth.decorators import login_required
from users_acc.models import *


#upatient files should not be in admin view (upload/download)

@login_required
def render_file_upload(request):
    if request.method == 'POST':
        up_form = Fileform(request.POST, request.FILES)
        if up_form.is_valid():
            fname = request.FILES["file"].name
            if request.FILES["file"].size <= 52428800:
                if len(fname) <= 100:
                    if (fname.endswith(".doc") or fname.endswith(".docx") or fname.endswith(".odf") or fname.endswith(".pdf") or fname.endswith(".jpeg") or fname.endswith(".jpg") or fname.endswith(".png") or fname.endswith(".bmp") or fname.endswith(".gif")):
                        #some logic ?????????
                        f=Uploaded_File()
                        f.usern=request.user
                        print(request.FILES["file"].name)
                        f.file_name = request.FILES["file"].name
                        f.file =request.FILES["file"]
                        f.save()
                        return render(request, 'upload_download/file_upload_Complete.html')
                    else:
                        context = {"errorMsg": "Unsupported File Type The Supported File Types are .doc, .docx, .odf, .pdf, .jpeg, .jpg, .png, .bmp, .gif"}
                        return render(request, 'upload_download/file_upload_Failed.html', context)
                else:
                    context = {"errorMsg": "Your File Name is Too Long"}
                    return render(request, 'upload_download/file_upload_Failed.html', context)
            else:
                context = {"errorMsg":"Your File is Too Big >50MB"}
                return render(request, 'upload_download/file_upload_Failed.html', context)
        else:
            return render(request, 'upload_download/file_upload_Failed.html')
    else:
        return render(request, 'upload_download/fileupload.html')

@login_required
def render_file_download(request):
    files = []
    if request.user.user_type == 1:
        for i in Uploaded_File.objects.all():
            # just find a way to query the request.user instead of all
            files.append({
                'FileName': i.file_name,
                'Uploader': i.usern.username,
                'file': i.file.url,
                'date_uploaded': i.date_created,
                'id': i.pk
            })
    elif request.user.user_type == 2:
        temp = Uploaded_File.objects.none()
        g = Uploaded_File.objects.filter(usern=request.user)
        # provider.user.last_name.
        # user.related name of profile.Patient_count
        if request.user.provider.Provider_type == 1:
            temp = Patient.objects.filter(doc_p=request.user.provider)
        elif request.user.provider.Provider_type == 2:
            temp = Patient.objects.filter(doc_d=request.user.provider)
        elif request.user.provider.Provider_type == 3:
            temp = Patient.objects.filter(doc_c=request.user.provider)
        for i in temp:
            t = Uploaded_File.objects.filter(usern=i.user)
            g = g | t
        for i in g:
            files.append({
                'FileName': i.file_name,
                'Uploader': i.usern.username,
                'file': i.file.url,
                'date_uploaded': i.date_created,
                'id': i.pk
            })
    elif request.user.user_type == 3:
        for i in Uploaded_File.objects.filter(usern=request.user):
            # just find a way to query the request.user instead of all
            files.append({
                'FileName': i.file_name,
                'Uploader': i.usern.username,
                'file': i.file.url,
                'date_uploaded': i.date_created,
                'id': i.pk
            })

    context = {
        'file_list': files
    }
    return render(request, 'upload_download/filedownload.html', context)


@login_required
def delete_file(request, id):
    if request.method == "POST":
        obj = get_object_or_404(Uploaded_File, id=id)
        obj.delete()
        return redirect('upload_download_file_download')
    context = {'file': id}
    return render(request, "upload_download/filedeleteconfirm.html", context)
