# -*- coding: utf-8 -*-
import codecs
import os.path
import re

from django.conf import settings
from django.http import HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import RequestContext


def view_ckeditor_templates(request):
    rx_name = re.compile('\<\!-- name="([^"]+)" \-\-\>')
    rx_image = re.compile('\<\!-- image="([^"]+)" \-\-\>|')
    rx_description = re.compile('\<\!-- description="([^"]+)" \-\-\>')
    templates_dir = getattr(settings, 'CKEDITOR_TEMPLATES_DIR', False)
    templates = []
    if templates_dir and not os.path.exists(templates_dir):
        templates_dir = os.path.join(settings.MEDIA_ROOT, templates_dir)
    if templates_dir and os.path.exists(templates_dir):
        files = [file for file in os.listdir(templates_dir) if file.endswith('.html')]
        for template in files:
            with codecs.open(os.path.join(templates_dir, template), 'r', 'utf-8') as tfp:
                template_content = tfp.read()
                template_data = {
                    'title': rx_name.findall(template_content)[0],
                    'image': rx_image.findall(template_content)[0],
                    'description': rx_description.findall(template_content)[0],
                    'body': template_content
                }
                templates.append(template_data)
        data = {
            'templates_dir': templates_dir,
            'templates': templates
        }
        context = RequestContext(request, data)
        return render_to_response('newsletter/utils/ckeditor_templates.html', context,
                                  mimetype='application/javascript')
    return HttpResponseNotFound('Templates not set')