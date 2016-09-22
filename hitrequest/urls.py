from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^list/$', views.list, name='list'),
    url(r'^delete/$', views.delete, name='delete'),
    url(r'^deleteAll/$', views.deleteAll, name='deleteAll'),
    url(r'^deleteAllHits/$', views.deleteAllHits, name='deleteAllHits'),
]
