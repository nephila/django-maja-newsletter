from django.conf.urls import url
from django.conf.urls import patterns


urlpatterns = patterns('emencia.django.newsletter.views.tinymce_utils',
    url(r'^templates/$', 'view_tinymce_templates', name='tinymce_templates_list'),
)
