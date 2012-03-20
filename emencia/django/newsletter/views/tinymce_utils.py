# views.py
from django.http import HttpResponse
from django.conf import settings
from emencia.django.newsletter import settings as e_settings
from filebrowser.base import FileObject

import os

def view_tinymce_templates(request):
    full_path = os.path.join(settings.MEDIA_ROOT,
                             e_settings.NEWSLETTER_TINYMCE_TEMPLATE_DIR)
    tmpl_dir = os.listdir(full_path)
    templates = []
    for tmpl in tmpl_dir:
        fileobject = FileObject(os.path.join(e_settings.NEWSLETTER_TINYMCE_TEMPLATE_DIR,tmpl))
        templates.append('["%s", "%s"]' % (fileobject.filename, fileobject._url_full()))
    
    page = """
    var tinyMCETemplateList = [
            // Name, URL, Description
            %s,
    ];
    """ % ",".join(templates)
    return HttpResponse(page, mimetype='text/javascript; charset=utf8')
