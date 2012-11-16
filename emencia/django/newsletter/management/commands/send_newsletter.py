"""Command for sending the newsletter"""
from django.conf import settings
from django.utils.translation import activate
from django.core.management.base import NoArgsCommand

from emencia.django.newsletter.mailer import Mailer
from emencia.django.newsletter.models import Newsletter
import codecs

class Command(NoArgsCommand):
    """Send the newsletter in queue"""
    help = 'Send the newsletter in queue'

    def handle_noargs(self, **options):
        verbose = int(options['verbosity'])

        if verbose:
            print 'Starting sending newsletters...'

        activate(settings.LANGUAGE_CODE)

        for newsletter in Newsletter.objects.exclude(
            status=Newsletter.DRAFT).exclude(status=Newsletter.SENT):
            mailer = Mailer(newsletter, verbose=verbose)
            if mailer.can_send:
                if verbose:
                    print 'Start emailing %s' % codecs.encode(newsletter.title,"utf-8")
                mailer.run()

        if verbose:
            print 'End session sending'
