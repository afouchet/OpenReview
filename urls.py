from django.conf.urls import url

from . import views

app_name = 'open_review'

urlpatterns = [
    url(r'^$', views.welcome, name='homepage'),
    url(r'^change_password/$', views.change_password, name='change_password'),
    url(r'^comment/(?P<publi_id>[0-9]+)$', views.comment_publi, name='comment'),
    url(r'^create_profile/$', views.create_profile_form, name='create_profile'),
    url(r'^created_profile/$', views.created_profile, name='created_profile'),
    url(r'^desc/(?P<publi_id>[0-9]+)$', views.publication_detail, name='article_desc'),
    url(r'^edit_profile/$', views.edit_profile_form, name='edit_profile'),
    url(r'^edited_profile/$', views.edited_profile, name='edited_profile'),
    url(r'^login/$', views.api_login, name='login'),
    url(r'^logout/$', views.api_logout, name='logout'),
    url(r'^log/$', views.log, name='logs'),
    url(r'^search/$', views.search, name='search'),
    url(r'^api/similar_articles/(?P<publi_id>[0-9]+)$', views.api_similar_articles,
        name='api_similar_articles'),
    url(r'^build_advanced_search/$', views.build_advanced_search, name='build_advanced_search'),
    url(r'^advanced_search/$', views.advanced_search, name='advanced_search'),
    url(r'^test/$', views.test, name='test'),
]
