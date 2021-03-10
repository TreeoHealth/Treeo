from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='messaging_home'),
    path('test/', views.test, name='test'),
    # path('outbox/', views.inbox, name='messaging_outbox'),
    # path('compose/', views.inbox, name='messaging_compose'),
    # path('reply/', views.inbox, name='messaging_reply'),
    # #path('convo/<id>', views.render_conversation, name='messaging_convo'),
    # path('undelete/<id>', views.undo_delete, name='messaging_undelete'),
    # path('delete/<id>', views.delete_message, name='messaging_delete'),
    # path('trash/', views.inbox, name='messaging_trash'),
]
