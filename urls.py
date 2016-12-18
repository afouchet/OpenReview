from django.conf.urls import url

from . import views

app_name = 'open_review'

urlpatterns = [
    url(r'^$', views.welcome, name='homepage'),
    url(r'^change_password/$', views.change_password, name='change_password'),
    url(r'^create_profile/$', views.create_profile_form, name='create_profile'),
    url(r'^created_profile/$', views.created_profile, name='created_profile'),
    url(r'^edit_profile/$', views.edit_profile_form, name='edit_profile'),
    url(r'^edited_profile/$', views.edited_profile, name='edited_profile'),
    url(r'^login/$', views.api_login, name='login'),
    url(r'^log/$', views.log, name='logs'),
]
