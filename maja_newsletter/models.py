"""Models for maja_newsletter"""
from smtplib import SMTP
from smtplib import SMTPHeloError
from datetime import datetime
from datetime import timedelta

from django.db import models
from django.utils.encoding import smart_str
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, User
from django.utils.encoding import force_unicode

from tagging.fields import TagField
from maja_newsletter.managers import ContactManager
from maja_newsletter.settings import BASE_PATH
from maja_newsletter.settings import MAILER_HARD_LIMIT
from maja_newsletter.settings import DEFAULT_HEADER_REPLY
from maja_newsletter.settings import DEFAULT_HEADER_SENDER
from maja_newsletter.utils.vcard import vcard_contact_export

# Patch for Python < 2.6
try:
    getattr(SMTP, 'ehlo_or_helo_if_needed')
except AttributeError:
    def ehlo_or_helo_if_needed(self):
        if self.helo_resp is None and self.ehlo_resp is None:
            if not (200 <= self.ehlo()[0] <= 299):
                (code, resp) = self.helo()
                if not (200 <= code <= 299):
                    raise SMTPHeloError(code, resp)
    SMTP.ehlo_or_helo_if_needed = ehlo_or_helo_if_needed


class SendBatch(models.Model):
    server = models.ForeignKey('SMTPServer')
    emails = models.IntegerField(_(u'emails batch'))
    date_create = models.DateTimeField(_(u'add date'), auto_now_add=True)
    user = models.ForeignKey(User, verbose_name=_(u'operator'), null=True)

    class Meta:
        verbose_name = _('email batch')
        verbose_name_plural = _('email batches')
        db_table = 'newsletter_sendbatch'

    def save(self, *args, **kwargs):
        if not self.pk: 
            self.server.emails_remains += self.emails
            self.server.save()
            super(SendBatch, self).save(*args, **kwargs)


class SMTPServer(models.Model):
    """Configuration of a SMTP server"""
    name = models.CharField(_('name'), max_length=255)
    host = models.CharField(_('server host'), max_length=255)
    user = models.CharField(_('server user'), max_length=128, blank=True,
                            help_text=_('Leave empty if the host is public.'))
    password = models.CharField(_('server password'), max_length=128, blank=True,
                                help_text=_('Leave empty if the host is public.'))
    port = models.IntegerField(_('server port'), default=25)
    tls = models.BooleanField(_('server use TLS'), default=False)

    headers = models.TextField(_('custom headers'), blank=True,
                               help_text=_('key1: value1 key2: value2, splitted by return line.\n'\
                                           'Useful for passing some tracking headers if your provider allows it.'))
    mails_hour = models.IntegerField(_('e-mail send rate'), help_text=_("E-Mail sending rate in messages per hour"),
                                     default=0)
    emails_remains = models.IntegerField(_('remaining e-mail'), help_text=_("Sendable E-Mail in the current account"),
                                         default=MAILER_HARD_LIMIT)

    def connect(self):
        """Connect the SMTP Server"""
        smtp = SMTP(smart_str(self.host), int(self.port))
        smtp.ehlo_or_helo_if_needed()
        if self.tls:
            smtp.starttls()
            smtp.ehlo_or_helo_if_needed()

        if self.user or self.password:
            smtp.login(smart_str(self.user), smart_str(self.password))
        return smtp

    def delay(self):
        """compute the delay (in seconds) between mails to ensure mails
        per hour limit is not reached

        :rtype: float
        """
        if not self.mails_hour:
            return 0.0
        else:
            return 3600.0 / self.mails_hour

    def credits(self):
        """Return how many mails the server can send"""
        if not self.mails_hour:
            return self.emails_remains

        last_hour = datetime.now() - timedelta(hours=1)
        sent_last_hour = ContactMailingStatus.objects.filter(
            models.Q(status=ContactMailingStatus.SENT) |
            models.Q(status=ContactMailingStatus.SENT_TEST),
            newsletter__server=self,
            creation_date__gte=last_hour).count()
        return self.mails_hour - sent_last_hour

    @property
    def custom_headers(self):
        if self.headers:
            headers = {}
            for header in self.headers.splitlines():
                if header:
                    key, value = header.split(':')
                    headers[key.strip()] = value.strip()
            return headers
        return {}

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.host)

    class Meta:
        verbose_name = _('SMTP server')
        verbose_name_plural = _('SMTP servers')
        db_table = 'newsletter_smtpserver'


class Contact(models.Model):
    """Contact for emailing"""
    email = models.EmailField(_('email'), max_length=150, unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)

    subscriber = models.BooleanField(_('subscriber'), default=True)
    valid = models.BooleanField(_('valid email'), default=True)
    tester = models.BooleanField(_('contact tester'), default=False)
    tags = TagField(_('tags'))

    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    creation_date = models.DateTimeField(_('creation date'), auto_now_add=True)
    modification_date = models.DateTimeField(_('modification date'), auto_now=True)

    objects = ContactManager()

    def subscriptions(self):
        """Return the user subscriptions"""
        return MailingList.objects.filter(subscribers=self)

    def unsubscriptions(self):
        """Return the user unsubscriptions"""
        return MailingList.objects.filter(unsubscribers=self)

    def vcard_format(self):
        return vcard_contact_export(self)

    def mail_format(self):
        if self.first_name and self.last_name:
            return '%s %s <%s>' % (self.last_name, self.first_name, self.email)
        return self.email
    mail_format.short_description = _('mail format')

    def get_absolute_url(self):
        if self.content_type and self.object_id:
            return self.content_object.get_absolute_url()
        return reverse('admin:maja_newsletter_contact_change', args=(self.pk,))

    def __unicode__(self):
        if self.first_name and self.last_name:
            contact_name = '%s %s' % (self.last_name, self.first_name)
        else:
            contact_name = self.email
        if self.tags:
            return '%s | %s' % (contact_name, self.tags)
        return contact_name

    class Meta:
        ordering = ('creation_date',)
        verbose_name = _('contact')
        verbose_name_plural = _('contacts')
        db_table = 'newsletter_contact'


class MailingList(models.Model):
    """Mailing list"""
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)

    subscribers = models.ManyToManyField(Contact, verbose_name=_('subscribers'),
                                         related_name='mailinglist_subscriber')
    unsubscribers = models.ManyToManyField(Contact, verbose_name=_('unsubscribers'),
                                           related_name='mailinglist_unsubscriber',
                                           null=True, blank=True)

    creation_date = models.DateTimeField(_('creation date'), auto_now_add=True)
    modification_date = models.DateTimeField(_('modification date'), auto_now=True)

    def subscribers_count(self):
        try:
            return self.subscribers.all().count()
        except ValueError:
            return 0
    subscribers_count.short_description = _('subscribers')

    def unsubscribers_count(self):
        try:
            return self.unsubscribers.all().count()
        except ValueError:
            return 0
    unsubscribers_count.short_description = _('unsubscribers')

    def expedition_set(self):
        unsubscribers_id = self.unsubscribers.values_list('id', flat=True)
        return self.subscribers.valid_subscribers().exclude(id__in=unsubscribers_id)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('-creation_date',)
        verbose_name = _('mailing list')
        verbose_name_plural = _('mailing lists')
        db_table = 'newsletter_mailinglist'


class Newsletter(models.Model):
    """Newsletter to be sended to contacts"""
    DRAFT = 0
    WAITING = 1
    SENDING = 2
    SENT = 4
    CANCELED = 5

    STATUS_CHOICES = ((DRAFT, _('draft')),
                      (WAITING, _('waiting sending')),
                      (SENDING, _('sending')),
                      (SENT, _('sent')),
                      (CANCELED, _('canceled')),
                      )

    title = models.CharField(_('title'), max_length=255,
                             help_text=_('You can use the "{{ UNIQUE_KEY }}" variable ' \
                                         'for unique identifier within the newsletter\'s title.'))
    content = models.TextField(_('content'), help_text=_('Or paste an URL.'),
                               default=_('<body>\n<!-- Edit your newsletter here -->\n</body>'))

    mailing_list = models.ForeignKey(MailingList, verbose_name=_('mailing list'))
    test_contacts = models.ManyToManyField(Contact, verbose_name=_('test contacts'),
                                           blank=True, null=True)

    server = models.ForeignKey(SMTPServer, verbose_name=_('smtp server'),
                               default=1)
    header_sender = models.CharField(_('sender'), max_length=255,
                                     default=DEFAULT_HEADER_SENDER)
    header_reply = models.CharField(_('reply to'), max_length=255,
                                    default=DEFAULT_HEADER_REPLY)

    status = models.IntegerField(_('status'), choices=STATUS_CHOICES, default=DRAFT)
    sending_date = models.DateTimeField(_('sending date'), default=datetime.now)

    slug = models.SlugField(help_text=_('Used for displaying the newsletter on the site.'),
                            max_length=255, unique=True)
    creation_date = models.DateTimeField(_('creation date'), auto_now_add=True)
    modification_date = models.DateTimeField(_('modification date'), auto_now=True)

    def mails_sent(self):
        return self.contactmailingstatus_set.filter(status=ContactMailingStatus.SENT).count()

    @models.permalink
    def get_absolute_url(self):
        return ('newsletter_newsletter_preview', (self.slug,))

    @models.permalink
    def get_historic_url(self):
        return ('newsletter_newsletter_historic', (self.slug,))

    @models.permalink
    def get_statistics_url(self):
        return ('newsletter_newsletter_statistics', (self.slug,))

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('-creation_date',)
        verbose_name = _('newsletter')
        verbose_name_plural = _('newsletters')
        permissions = (('can_change_status', 'Can change status'),)
        db_table = 'newsletter_newsletter'


class Link(models.Model):
    """Link sended in a newsletter"""
    title = models.CharField(_('title'), max_length=255)
    url = models.CharField(_('url'), max_length=255)

    creation_date = models.DateTimeField(_('creation date'), auto_now_add=True)

    def get_absolute_url(self):
        return self.url

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('-creation_date',)
        verbose_name = _('link')
        verbose_name_plural = _('links')
        db_table = 'newsletter_link'


class Attachment(models.Model):
    """Attachment file in a newsletter"""

    def get_newsletter_storage_path(self, filename):
        filename = force_unicode(filename)
        return '/'.join([BASE_PATH, self.newsletter.slug, filename])

    newsletter = models.ForeignKey(Newsletter, verbose_name=_('newsletter'))
    title = models.CharField(_('title'), max_length=255)
    file_attachment = models.FileField(_('file to attach'), max_length=255,
                                       upload_to=get_newsletter_storage_path)

    class Meta:
        verbose_name = _('attachment')
        verbose_name_plural = _('attachments')
        db_table = 'newsletter_attachment'

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return self.file_attachment.url


class ContactMailingStatus(models.Model):
    """Status of the reception"""
    SENT_TEST = -1
    SENT = 0
    ERROR = 1
    INVALID = 2
    OPENED = 4
    OPENED_ON_SITE = 5
    LINK_OPENED = 6
    UNSUBSCRIPTION = 7

    STATUS_CHOICES = ((SENT_TEST, _('sent in test')),
                      (SENT, _('sent')),
                      (ERROR, _('error')),
                      (INVALID, _('invalid email')),
                      (OPENED, _('opened')),
                      (OPENED_ON_SITE, _('opened on site')),
                      (LINK_OPENED, _('link opened')),
                      (UNSUBSCRIPTION, _('unsubscription')),
                      )

    newsletter = models.ForeignKey(Newsletter, verbose_name=_('newsletter'))
    contact = models.ForeignKey(Contact, verbose_name=_('contact'))
    status = models.IntegerField(_('status'), choices=STATUS_CHOICES)
    link = models.ForeignKey(Link, verbose_name=_('link'),
                             blank=True, null=True)

    creation_date = models.DateTimeField(_('creation date'), auto_now_add=True)

    def __unicode__(self):
        return '%s : %s : %s' % (self.newsletter.__unicode__(),
                                 self.contact.__unicode__(),
                                 self.get_status_display())

    class Meta:
        ordering = ('-creation_date',)
        verbose_name = _('contact mailing status')
        verbose_name_plural = _('contact mailing statuses')
        db_table = 'newsletter_contactmailingstatus'


class WorkGroup(models.Model):
    """Work Group for privatization of the ressources"""
    name = models.CharField(_('name'), max_length=255)
    group = models.ForeignKey(Group, verbose_name=_('permissions group'))

    contacts = models.ManyToManyField(Contact, verbose_name=_('contacts'),
                                      blank=True, null=True)
    mailinglists = models.ManyToManyField(MailingList, verbose_name=_('mailing lists'),
                                          blank=True, null=True)
    newsletters = models.ManyToManyField(Newsletter, verbose_name=_('newsletters'),
                                         blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('workgroup')
        verbose_name_plural = _('workgroups')
        db_table = 'newsletter_workgroup'
