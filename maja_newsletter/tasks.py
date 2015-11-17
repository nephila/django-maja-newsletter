from __future__ import absolute_import
from celery import shared_task

from maja_newsletter.mailer import Mailer
from maja_newsletter.models import Newsletter


@shared_task
def celery_send_newsletter(newsletter):
    mailer = Mailer(newsletter)
    if mailer.can_send:
        mailer.run(send_all=True)
