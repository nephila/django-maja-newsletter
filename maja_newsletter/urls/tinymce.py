from django.conf.urls import url
from django.conf.urls import patterns


urlpatterns = patterns('maja_newsletter.views.tinymce_utils',
    url(r'^templates/$', 'view_tinymce_templates', name='tinymce_templates_list'),
)
