from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^index/$', views.index, name='index'),
    url(r'^delete/$', views.delete, name='delete'),
    url(r'^deleteAll/$', views.deleteAll, name='deleteAll'),
    url(r'^deleteAllHits/$', views.deleteAllHits, name='deleteAllHits'),
    url(r'^approveAllHits/$', views.approveAllHits, name='approveAllHits'),
]
