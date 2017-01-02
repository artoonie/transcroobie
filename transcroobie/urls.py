from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView


urlpatterns = [
    url(r'^hit/', include('hit.urls')),
    url(r'^hitrequest/', include('hitrequest.urls', namespace='hitrequest')),
    url(r'^$', RedirectView.as_view(pattern_name='hitrequest:index', permanent=True)),
    url(r'^admin/', admin.site.urls),
    url(r'^oauth/', include('social.apps.django_app.urls', namespace='social')),
    url(r'^login', auth_views.login, name='login'),
    url(r'^logout', auth_views.login, name='logout'), # logout redirects to in
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
