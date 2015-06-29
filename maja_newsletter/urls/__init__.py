"""Default urls for the maja_newsletter"""
from django.conf.urls import url
from django.conf.urls import include
from django.conf.urls import patterns

urlpatterns = patterns('',
   url(r'^mailing/', include('maja_newsletter.urls.mailing_list')),
   url(r'^tracking/', include('maja_newsletter.urls.tracking')),
   url(r'^statistics/', include('maja_newsletter.urls.statistics')),
   url(r'^', include('maja_newsletter.urls.newsletter')),
)

