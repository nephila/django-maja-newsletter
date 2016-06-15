from __future__ import absolute_import

import shutil

import codecs
import os.path
from tempfile import mkdtemp

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage

from maja_newsletter.mailer import Mailer
from maja_newsletter.models import Newsletter
from maja_newsletter.utils.excel import make_excel_content
from maja_newsletter.utils.vcard import make_vcard_content
from maja_newsletter.settings import EXPORT_FILE_NAME, EXPORT_EMAIL_SUBJECT


@shared_task
def celery_send_newsletter(newsletter_id, *args, **kwargs):
    try:
        newsletter = Newsletter.objects.get(pk=newsletter_id)
        mailer = Mailer(newsletter)
        if mailer.can_send:
            mailer.run(send_all=True)
        return mailer.can_send
    except Newsletter.DoesNotExist:
        return False


@shared_task
def export_excel(data, recipient, export_name=None, headers=None, force_csv=False, encoding='utf8'):
    filedir = mkdtemp()
    output_file = os.path.join(filedir, export_name)
    with open(output_file, 'wb') as output:
        output, mimetype, file_ext = make_excel_content(data, output, headers, force_csv, encoding)
    final_path = '{0}.{1}'.format(output_file, file_ext)
    shutil.copyfile(output_file, final_path)
    testo = EXPORT_FILE_NAME
    message = EmailMessage(EXPORT_EMAIL_SUBJECT, testo, settings.DEFAULT_FROM_EMAIL, [recipient])
    message.attach_file(final_path, mimetype=mimetype)
    message.send()
    shutil.rmtree(filedir)


@shared_task
def export_vcard(data, recipient, export_name=None):
    filedir = mkdtemp()
    output_file = os.path.join(filedir, export_name)
    with open(output_file, 'wb') as output:
        output, mimetype, file_ext = make_vcard_content(data, output)
    final_path = '{0}.{1}'.format(output_file, file_ext)
    shutil.copyfile(output_file, final_path)
    testo = EXPORT_FILE_NAME
    message = EmailMessage(EXPORT_EMAIL_SUBJECT, testo, settings.DEFAULT_FROM_EMAIL, [recipient])
    message.attach_file(final_path, mimetype=mimetype)
    message.send()
    shutil.rmtree(filedir)