from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as dauth_views
from . import views as users_acc_views

urlpatterns = [
#path('login/', dauth_views.LoginView.as_view(template_name='login.html'), name='login'),
path('logout/', dauth_views.LogoutView.as_view(template_name='users_acc/logout.html'), name='logout'),
path('password-reset/', dauth_views.PasswordResetView.as_view(template_name='users_acc/pass_reset.html'), name='pass_reset'),
path('password-reset/done/', dauth_views.PasswordResetDoneView.as_view(template_name='users_acc/pass_reset_done.html'),name='password_reset_done'),
path('password-reset/confirm/<uidb64>/<token>/',dauth_views.PasswordResetConfirmView.as_view(template_name='users_acc/pass_reset_confirm.html'), name='password_reset_confirm'),
path('password-reset-complete/',dauth_views.PasswordResetCompleteView.as_view(template_name='users_acc/pass_reset_complete.html'),name='password_reset_complete'),
path('register/', users_acc_views.register, name='register'),
path('account_activation_sent/', users_acc_views.account_activation_sent, name='account_activation_sent'),
path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',users_acc_views.activate, name='activate'),
path('profile/', users_acc_views.profile, name='profile'),
path('edit_profile/', users_acc_views.edit_profile, name='edit_profile'),
path('button/', users_acc_views.button, name='button'),
path('', users_acc_views.home, name='home'),
path('login/', users_acc_views.loginuser, name='login'),
path('doctor_registration/', users_acc_views.doctor_registration, name='doctor_registration'),
path('admin_remove_provider/<id>/<id2>', users_acc_views.admin_remove_provider, name='admin_remove_provider'),
path('admin_assign/', users_acc_views.admin_view, name='admin_view'),
path('admin_display_team/<id>/', users_acc_views.admin_display_team, name='admin_display_team'),
path('admin_approve_provider_render/', users_acc_views.admin_approve_provider_render, name='admin_approve_provider_render'),
path('admin_approve_provider/<id>', users_acc_views.admin_approve_provider, name='admin_approve_provider'),
path('admin_revoke_provider/<id>', users_acc_views.admin_revoke_provider, name='admin_revoke_provider'),
]