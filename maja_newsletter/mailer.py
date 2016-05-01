"""Mailer for maja_newsletter"""
import mimetypes
import re
import sys
import threading
import time
from StringIO import StringIO
from email import message_from_file, utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from random import sample
from smtplib import SMTPRecipientsRefused

from datetime import timedelta
from django.contrib.sites.models import Site
from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils.encoding import smart_text
from django.utils.timezone import now
from email.mime.Encoders import encode_base64
from email.mime.MIMEAudio import MIMEAudio
from email.mime.MIMEBase import MIMEBase
from email.mime.MIMEImage import MIMEImage
from html2text import html2text as html2text_orig

from maja_newsletter.models import ContactMailingStatus
from maja_newsletter.models import Newsletter
from maja_newsletter.settings import INCLUDE_UNSUBSCRIPTION
from maja_newsletter.settings import \
     RESTART_CONNECTION_BETWEEN_SENDING
from maja_newsletter.settings import SLEEP_BETWEEN_SENDING
from maja_newsletter.settings import TRACKING_IMAGE
from maja_newsletter.settings import TRACKING_IMAGE_FORMAT
from maja_newsletter.settings import TRACKING_LINKS
from maja_newsletter.settings import UNIQUE_KEY_CHAR_SET
from maja_newsletter.settings import UNIQUE_KEY_LENGTH
from maja_newsletter.utils.newsletter import body_insertion
from maja_newsletter.utils.newsletter import track_links
from maja_newsletter.utils.tokens import tokenize

if not hasattr(timedelta, 'total_seconds'):
    def total_seconds(td):
        return ((td.microseconds +
                 (td.seconds + td.days * 24 * 3600) * 1000000) /
                1000000.0)
else:
    total_seconds = lambda td: td.total_seconds()


LINK_RE = re.compile(r"https?://([^ \n]+\n)+[^ \n]+", re.MULTILINE)


def html2text(html):
    """Use html2text but repair newlines cutting urls.
    Need to use this hack until
    https://github.com/aaronsw/html2text/issues/#issue/7 is not fixed"""
    txt = html2text_orig(html)
    links = list(LINK_RE.finditer(txt))
    out = StringIO()
    pos = 0
    for l in links:
        out.write(txt[pos:l.start()])
        out.write(l.group().replace('\n', ''))
        pos = l.end()
    out.write(txt[pos:])
    return out.getvalue()


class NewsLetterSender(object):

    def __init__(self, newsletter, test=False, verbose=0):
        self.test = test
        self.verbose = verbose
        self.newsletter = newsletter
        self.newsletter_template = Template(self.newsletter.content)
        self.title_template = Template(self.newsletter.title)

    def build_message(self, contact):
        """
        Build the email as a multipart message containing
        a multipart alternative for text (plain, HTML) plus
        all the attached files.
        """
        content_html = self.build_email_content(contact)
        content_text = html2text(content_html)

        message = MIMEMultipart()

        message['Message-Id'] = utils.make_msgid()
        message['Subject'] = self.build_title_content(contact)
        message['From'] = smart_text(self.newsletter.header_sender)
        message['Reply-to'] = smart_text(self.newsletter.header_reply)
        message['To'] = contact.mail_format()
        message['Date'] = utils.formatdate()

        message_alt = MIMEMultipart('alternative')
        message_alt.attach(MIMEText(smart_text(content_text), 'plain', 'UTF-8'))
        message_alt.attach(MIMEText(smart_text(content_html), 'html', 'UTF-8'))
        message.attach(message_alt)

        for attachment in self.attachments:
            message.attach(attachment)

        for header, value in self.newsletter.server.custom_headers.items():
            message[header] = value

        return message

    def build_attachments(self):
        """Build email's attachment messages"""
        attachments = []

        for attachment in self.newsletter.attachment_set.all():
            ctype, encoding = mimetypes.guess_type(attachment.file_attachment.path)

            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'

            maintype, subtype = ctype.split('/', 1)

            fd = open(attachment.file_attachment.path, 'rb')
            if maintype == 'text':
                message_attachment = MIMEText(fd.read(), _subtype=subtype)
            elif maintype == 'message':
                message_attachment = message_from_file(fd)
            elif maintype == 'image':
                message_attachment = MIMEImage(fd.read(), _subtype=subtype)
            elif maintype == 'audio':
                message_attachment = MIMEAudio(fd.read(), _subtype=subtype)
            else:
                message_attachment = MIMEBase(maintype, subtype)
                message_attachment.set_payload(fd.read())
                encode_base64(message_attachment)
            fd.close()
            message_attachment.add_header('Content-Disposition', 'attachment',
                                          filename=attachment.title)
            attachments.append(message_attachment)

        return attachments

    def build_title_content(self, contact):
        """Generate the email title for a contact"""
        context = Context({'contact': contact,
                           'UNIQUE_KEY': ''.join(sample(UNIQUE_KEY_CHAR_SET,
                                                        UNIQUE_KEY_LENGTH))})
        title = self.title_template.render(context)
        return title

    def build_email_content(self, contact):
        """Generate the mail for a contact"""
        uidb36, token = tokenize(contact)
        context = Context({'contact': contact,
                           'domain': Site.objects.get_current().domain,
                           'newsletter': self.newsletter,
                           'tracking_image_format': TRACKING_IMAGE_FORMAT,
                           'uidb36': uidb36, 'token': token})
        content = self.newsletter_template.render(context)

        if TRACKING_LINKS:
            content = track_links(content, context)
        link_site = render_to_string('newsletter/newsletter_link_site.html', context)
        content = body_insertion(content, link_site)

        if INCLUDE_UNSUBSCRIPTION:
            unsubscription = render_to_string('newsletter/newsletter_link_unsubscribe.html', context)
            content = body_insertion(content, unsubscription, end=True)
        if TRACKING_IMAGE:
            image_tracking = render_to_string('newsletter/newsletter_image_tracking.html', context)
            content = body_insertion(content, image_tracking, end=True)
        return smart_text(content)

    def update_newsletter_status(self):
        """Update the status of the newsletter"""
        if self.test:
            return

        if self.newsletter.status == Newsletter.WAITING:
            self.newsletter.status = Newsletter.SENDING
        if self.newsletter.status == Newsletter.SENDING and \
               self.newsletter.mails_sent() >= \
               self.newsletter.mailing_list.expedition_set().count():
            self.newsletter.status = Newsletter.SENT
        self.newsletter.save()

    @property
    def can_send(self):
        """Check if the newsletter can be sent"""
        if self.test:
            return True

        if self.newsletter.sending_date <= now() and \
                (self.newsletter.status == Newsletter.WAITING or \
                             self.newsletter.status == Newsletter.SENDING):
            return True

        return False

    def expedition_list(self, send_all=False):
        """Build the expedition list"""
        if self.test:
            return self.newsletter.test_contacts.all()

        already_sent = ContactMailingStatus.objects.filter(status=ContactMailingStatus.SENT,
                                                           newsletter=self.newsletter).values_list('contact__id', flat=True)
        expedition_list = self.newsletter.mailing_list.expedition_set().exclude(id__in=already_sent)
        return expedition_list

    def update_contact_status(self, contact, exception):
        if exception is None:
            status = (self.test
                      and ContactMailingStatus.SENT_TEST
                      or ContactMailingStatus.SENT)
        elif isinstance(exception, (UnicodeError, SMTPRecipientsRefused)):
            status = ContactMailingStatus.INVALID
            contact.valid = False
            contact.save()
        else:
            # signal error
            print >>sys.stderr, 'smtp connection raises %s' % exception
            status = ContactMailingStatus.ERROR

        ContactMailingStatus.objects.create(
            newsletter=self.newsletter, contact=contact, status=status)


class Mailer(NewsLetterSender):
    """Mailer for generating and sending newsletters
    In test mode the mailer always send mails but do not log it"""
    smtp = None

    def run(self, send_all=False):
        """Send the mails"""
        if not self.can_send:
            return

        if not self.smtp:
            self.smtp_connect()

        self.attachments = self.build_attachments()
        start = now()
        delay = self.newsletter.server.delay()

        expedition_list = self.expedition_list(send_all)

        number_of_recipients = len(expedition_list)
        if self.verbose:
            print('%i emails will be sent' % number_of_recipients)

        i = 1
        for contact in expedition_list:
            if not ContactMailingStatus.objects.filter(
                    status=ContactMailingStatus.SENT, contact_id=contact.pk,
                    newsletter_id=self.newsletter.pk
            ).exists():
                if self.verbose:
                    print('- Processing %s/%s (%s)' % (i, number_of_recipients, contact.pk))

                try:
                    message = self.build_message(contact)
                    self.smtp.sendmail(smart_text(self.newsletter.header_sender),
                                       contact.email,
                                       message.as_string())
                except Exception, e:
                    exception = e
                    if self.verbose:
                        print(e)
                    if type(e) == UnicodeEncodeError:
                        raise e
                else:
                    exception = None

                self.update_contact_status(contact, exception)

                sleep_time = (delay * i - total_seconds(now() - start))

                if SLEEP_BETWEEN_SENDING and sleep_time:
                    time.sleep(sleep_time)
                if RESTART_CONNECTION_BETWEEN_SENDING:
                    self.smtp.quit()
                    self.smtp_connect()

                i += 1

        self.smtp.quit()
        self.update_newsletter_status()

    def smtp_connect(self):
        """Make a connection to the SMTP"""
        self.smtp = self.newsletter.server.connect()

    def expedition_list(self, send_all=False):
        """Build the expedition list"""
        credits = self.newsletter.server.credits()
        if credits <= 0:
            return []
        result_list = super(Mailer, self).expedition_list()
        if not send_all:
            result_list = result_list[:credits]
        return result_list

    @property
    def can_send(self):
        """Check if the newsletter can be sent"""
        if self.newsletter.server.credits() <= 0:
            return False
        return super(Mailer, self).can_send


class SMTPMailer(object):
    """for generating and sending newsletters

    SMTPMailer takes the problem on a different basis than Mailer, it use
    a SMTP server and make a roundrobin over all newsletters to be sent
    dispatching it's send command to smtp server regularly over time to
    reach the limit.

    It is more robust in term of predictability.

    In test mode the mailer always send mails but do not log it"""

    smtp = None

    def __init__(self, server, test=False, verbose=0):
        self.start = now()
        self.server = server
        self.test = test
        self.verbose = verbose
        self.stop_event = threading.Event()

    def run(self, send_all=False):
        """send mails
        """
        sending = dict()
        roundrobin = []

        if not self.smtp:
            self.smtp_connect()

        delay = self.server.delay()

        i = 1
        sleep_time = 0
        while (not self.stop_event.wait(sleep_time) and
               not self.stop_event.is_set()):
            if not roundrobin:
                candidates = self.get_candidates(send_all)
                # refresh the list
                for expedition in candidates:
                    if expedition.id not in sending and expedition.can_send:
                        sending[expedition.id] = expedition()

                roundrobin = list(sending.keys())

            if roundrobin:
                nl_id = roundrobin.pop()
                nl = sending[nl_id]

                if i == 1:
                    self.smtp.quit()
                    self.smtp_connect()
                try:
                    self.smtp.sendmail(*nl.next())
                except StopIteration:
                    del sending[nl_id]
                except Exception, e:
                    nl.throw(e)
                else:
                    nl.next()

                sleep_time = (delay * i -
                              total_seconds(now() - self.start))
                if SLEEP_BETWEEN_SENDING:
                    sleep_time = max(time.sleep(SLEEP_BETWEEN_SENDING), sleep_time)
                if RESTART_CONNECTION_BETWEEN_SENDING:
                    self.smtp.quit()
                    self.smtp_connect()
                i += 1
            else:
                # no work, sleep a bit and some reset
                sleep_time = 6
                i = 1
                self.start = now()

            if sleep_time < 0:
                sleep_time = 0

        self.smtp.quit()

    def get_candidates(self, send_all=False):
        """get candidates NL"""
        return [NewsLetterExpedition(nl, self, send_all)
                for nl in Newsletter.objects.filter(server=self.server)]

    def smtp_connect(self):
        """Make a connection to the SMTP"""
        self.smtp = self.server.connect()


class NewsLetterExpedition(NewsLetterSender):
    """coroutine that will give messages to be sent with mailer

    between to message it alternate with None so that
    the mailer give it a chance to save status to db
    """

    def __init__(self, newsletter, mailer, send_all=False):
        super(NewsLetterExpedition, self).__init__(
                        newsletter, test=mailer.test, verbose=mailer.verbose)
        self.mailer = mailer
        self.id = newsletter.id
        self.send_all = send_all

    def __call__(self):
        """iterator on messages to be sent
        """
        newsletter = self.newsletter

        title = 'smtp-%s (%s), nl-%s (%s)' % (
                        self.mailer.server.id, self.mailer.server.name[:10],
                        newsletter.id, newsletter.title[:10])
        # ajust len
        title = '%-30s' % title

        self.attachments = self.build_attachments()

        expedition_list = self.expedition_list(self.send_all)

        number_of_recipients = len(expedition_list)
        if self.verbose:
            print('%s %s: %i emails will be sent' % (
                now().strftime('%Y-%m-%d'),
                title, number_of_recipients))

        try:
            i = 1
            for contact in expedition_list:
                if self.verbose:
                    print('%s %s: processing %s/%s (%s)' % (
                        now().strftime('%H:%M:%S'),
                        title, i, number_of_recipients, contact.pk))
                try:
                    message = self.build_message(contact)
                    yield (smart_text(self.newsletter.header_sender),
                                       contact.email,
                                       message.as_string())
                except Exception, e:
                    exception = e
                    if self.verbose:
                        print(e)
                    if type(e) == UnicodeEncodeError:
                        raise e
                else:
                    exception = None

                self.update_contact_status(contact, exception)
                i += 1
                # this one permits us to save to database imediately
                # and acknoledge eventual exceptions
                yield None
        finally:
            self.update_newsletter_status()
