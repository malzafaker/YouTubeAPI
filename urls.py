from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from apps.youtube.youtube import authorize, oauth2callback, revoke, clear_credentials

urlpatterns = [

    url(r'^authorize/$', login_required(authorize)),
    url(r'^oauth2callback/$', login_required(oauth2callback)),
    url(r'^revoke/$', login_required(revoke)),
    url(r'^clear_credentials/$', login_required(clear_credentials)),

]
