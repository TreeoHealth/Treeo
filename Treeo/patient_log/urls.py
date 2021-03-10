from django.urls import path
from . import views
# from .views import *

urlpatterns = [
    path('', views.patientlog, name='patientlog'),
    # path('Chart', views.chart, name='seechart'),
    # path('charts', Circle.as_view(), name='chart_json'),
    path('log-chart/<id>', views.line_chart_Week, name='log-chart'),
    path('edit_log/<id>', views.edit_log, name='edit_log'),
]