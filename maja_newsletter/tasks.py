from __future__ import absolute_import
from celery import shared_task

from maja_newsletter.mailer import Mailer
from maja_newsletter.models import Newsletter


@shared_task
def celery_send_newsletter(newsletter, *args, **kwargs):
    mailer = Mailer(newsletter)
    if mailer.can_send:
        mailer.run(send_all=True)
    return mailer.can_send