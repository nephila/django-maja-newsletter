"""Command for sending the newsletter"""
from threading import Thread
import functools
import signal
import sys

from django.conf import settings
from django.utils.translation import activate
from django.core import signals
from django.core.management.base import NoArgsCommand

from maja_newsletter.mailer import SMTPMailer
from maja_newsletter.models import SMTPServer


class Command(NoArgsCommand):
    """Send the newsletter in queue"""
    help = 'Send the newsletter in queue'

    def handle_noargs(self, **options):
        verbose = int(options['verbosity'])
        send_all = True

        if verbose:
            print 'Starting sending newsletters...'

        activate(settings.LANGUAGE_CODE)

        senders = SMTPServer.objects.all()
        workers = []

        for sender in senders:
            worker = SMTPMailer(sender, verbose=verbose)
            thread = Thread(target=functools.partial(worker.run, send_all), name=sender.name)
            workers.append((worker, thread))

        handler = term_handler(workers)
        for s in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(s, handler)

        # first close current connection
        signals.request_finished.send(sender=self.__class__)

        for worker, thread in workers:
            thread.start()

        signal.pause()  # wait for sigterm

        for worker, thread in workers:
            if thread.is_alive():
                thread.join()

        sys.exit(0)


def term_handler(workers):

    def handler(signum, frame):
        for worker, thread in workers:
            worker.stop_event.set()

    return handler
