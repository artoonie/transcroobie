from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^fixHIT$', views.fixHIT, name='fixHIT'),
    url(r'^checkHIT$', views.checkHIT, name='checkHIT'),
]
