"""Unit tests for emencia.django.newsletter"""
from datetime import datetime
from datetime import timedelta
from django.contrib.sites.models import Site
from django.template import Context
from django.template.defaultfilters import slugify
from emencia.django.newsletter.utils.newsletter import track_links
from tempfile import NamedTemporaryFile

from django.test import TestCase
from django.http import Http404
from django.db import IntegrityError
from django.core.files import File

from emencia.django.newsletter.mailer import Mailer
from emencia.django.newsletter.models import Link
from emencia.django.newsletter.models import Contact
from emencia.django.newsletter.models import MailingList
from emencia.django.newsletter.models import SMTPServer
from emencia.django.newsletter.models import Newsletter
from emencia.django.newsletter.models import Attachment
from emencia.django.newsletter.models import ContactMailingStatus
from emencia.django.newsletter.utils.tokens import tokenize
from emencia.django.newsletter.utils.tokens import untokenize
from emencia.django.newsletter.utils.statistics import get_newsletter_opening_statistics
from emencia.django.newsletter.utils.statistics import get_newsletter_on_site_opening_statistics
from emencia.django.newsletter.utils.statistics import get_newsletter_unsubscription_statistics
from emencia.django.newsletter.utils.statistics import get_newsletter_clicked_link_statistics
from emencia.django.newsletter.utils.statistics import get_newsletter_top_links
from emencia.django.newsletter.utils.statistics import get_newsletter_statistics


class FakeSMTP(object):
    mails_sent = 0

    def sendmail(self, *ka, **kw):
        self.mails_sent += 1
        return {}

    def quit(*ka, **kw):
        pass


class SMTPServerTestCase(TestCase):
    """Tests for the SMTPServer model"""

    def setUp(self):
        self.server = SMTPServer.objects.create(name='Test SMTP',
                                                host='smtp.domain.com')
        self.server_2 = SMTPServer.objects.create(name='Test SMTP 2',
                                                  host='smtp.domain2.com')
        self.contact = Contact.objects.create(email='test@domain.com')
        self.mailinglist = MailingList.objects.create(name='Test MailingList')
        self.mailinglist.subscribers.add(self.contact)
        self.newsletter = Newsletter.objects.create(title='Test Newsletter',
                                                    content='Test Newsletter Content',
                                                    mailing_list=self.mailinglist,
                                                    server=self.server, slug='test-nl')

        self.newsletter_2 = Newsletter.objects.create(title='Test Newsletter 2',
                                                      content='Test Newsletter 2 Content',
                                                      mailing_list=self.mailinglist,
                                                      server=self.server, slug='test-nl-2')
        self.newsletter_3 = Newsletter.objects.create(title='Test Newsletter 2',
                                                      content='Test Newsletter 2 Content',
                                                      mailing_list=self.mailinglist,
                                                      server=self.server_2, slug='test-nl-3')

    def test_credits(self):
        # Testing unlimited account
        self.assertEquals(self.server.credits(), 10000)
        # Testing default limit
        self.server.mails_hour = 42
        self.assertEquals(self.server.credits(), 42)

        # Testing credits status, with multiple server case
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contact,
                                            status=ContactMailingStatus.SENT)
        self.assertEquals(self.server.credits(), 41)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contact,
                                            status=ContactMailingStatus.SENT_TEST)
        self.assertEquals(self.server.credits(), 40)
        # Testing with a fake status
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contact,
                                            status=ContactMailingStatus.ERROR)
        self.assertEquals(self.server.credits(), 40)
        # Testing with a second newsletter sharing the server
        ContactMailingStatus.objects.create(newsletter=self.newsletter_2,
                                            contact=self.contact,
                                            status=ContactMailingStatus.SENT)
        self.assertEquals(self.server.credits(), 39)
        # Testing with a third newsletter with another server
        ContactMailingStatus.objects.create(newsletter=self.newsletter_3,
                                            contact=self.contact,
                                            status=ContactMailingStatus.SENT)
        self.assertEquals(self.server.credits(), 39)

    def test_custom_headers(self):
        self.assertEquals(self.server.custom_headers, {})
        self.server.headers = 'key_1: val_1\r\nkey_2   :   val_2'
        self.assertEquals(len(self.server.custom_headers), 2)


class ContactTestCase(TestCase):
    """Tests for the Contact model"""

    def setUp(self):
        self.mailinglist_1 = MailingList.objects.create(name='Test MailingList')
        self.mailinglist_2 = MailingList.objects.create(name='Test MailingList 2')

    def test_unique(self):
        Contact(email='test@domain.com').save()
        self.assertRaises(IntegrityError, Contact(email='test@domain.com').save)

    def test_mail_format(self):
        contact = Contact(email='test@domain.com')
        self.assertEquals(contact.mail_format(), 'test@domain.com')
        contact = Contact(email='test@domain.com', first_name='Toto')
        self.assertEquals(contact.mail_format(), 'test@domain.com')
        contact = Contact(email='test@domain.com', first_name='Toto', last_name='Titi')
        self.assertEquals(contact.mail_format(), 'Titi Toto <test@domain.com>')

    def test_vcard_format(self):
        contact = Contact(email='test@domain.com', first_name='Toto', last_name='Titi')
        self.assertEquals(contact.vcard_format(), 'BEGIN:VCARD\r\nVERSION:3.0\r\n'\
                          'EMAIL;TYPE=INTERNET:test@domain.com\r\nFN:Toto Titi\r\n'\
                          'N:Titi;Toto;;;\r\nEND:VCARD\r\n')

    def test_subscriptions(self):
        contact = Contact.objects.create(email='test@domain.com')
        self.assertEquals(len(contact.subscriptions()), 0)

        self.mailinglist_1.subscribers.add(contact)
        self.assertEquals(len(contact.subscriptions()), 1)
        self.mailinglist_2.subscribers.add(contact)
        self.assertEquals(len(contact.subscriptions()), 2)

    def test_unsubscriptions(self):
        contact = Contact.objects.create(email='test@domain.com')
        self.assertEquals(len(contact.unsubscriptions()), 0)

        self.mailinglist_1.unsubscribers.add(contact)
        self.assertEquals(len(contact.unsubscriptions()), 1)
        self.mailinglist_2.unsubscribers.add(contact)
        self.assertEquals(len(contact.unsubscriptions()), 2)


class MailingListTestCase(TestCase):
    """Tests for the MailingList model"""

    def setUp(self):
        self.contact_1 = Contact.objects.create(email='test1@domain.com')
        self.contact_2 = Contact.objects.create(email='test2@domain.com', valid=False)
        self.contact_3 = Contact.objects.create(email='test3@domain.com', subscriber=False)
        self.contact_4 = Contact.objects.create(email='test4@domain.com')

    def test_subscribers_count(self):
        mailinglist = MailingList(name='Test MailingList')
        mailinglist.save()
        self.assertEquals(mailinglist.subscribers_count(), 0)
        mailinglist.subscribers.add(self.contact_1, self.contact_2, self.contact_3)
        self.assertEquals(mailinglist.subscribers_count(), 3)

    def test_unsubscribers_count(self):
        mailinglist = MailingList.objects.create(name='Test MailingList')
        self.assertEquals(mailinglist.unsubscribers_count(), 0)
        mailinglist.unsubscribers.add(self.contact_1, self.contact_2, self.contact_3)
        self.assertEquals(mailinglist.unsubscribers_count(), 3)

    def test_expedition_set(self):
        mailinglist = MailingList.objects.create(name='Test MailingList')
        self.assertEquals(len(mailinglist.expedition_set()), 0)
        mailinglist.subscribers.add(self.contact_1, self.contact_2, self.contact_3)
        self.assertEquals(len(mailinglist.expedition_set()), 1)
        mailinglist.subscribers.add(self.contact_4)
        self.assertEquals(len(mailinglist.expedition_set()), 2)
        mailinglist.unsubscribers.add(self.contact_4)
        self.assertEquals(len(mailinglist.expedition_set()), 1)


class NewsletterTestCase(TestCase):
    """Tests for the Newsletter model"""

    def setUp(self):
        self.server = SMTPServer.objects.create(name='Test SMTP',
                                                host='smtp.domain.com')
        self.contact = Contact.objects.create(email='test@domain.com')
        self.mailinglist = MailingList.objects.create(name='Test MailingList')
        self.newsletter = Newsletter.objects.create(title='Test Newsletter',
                                                    content='Test Newsletter Content',
                                                    mailing_list=self.mailinglist,
                                                    server=self.server)

    def test_mails_sent(self):
        self.assertEquals(self.newsletter.mails_sent(), 0)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contact,
                                            status=ContactMailingStatus.SENT)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contact,
                                            status=ContactMailingStatus.SENT_TEST)
        self.assertEquals(self.newsletter.mails_sent(), 1)


class TokenizationTestCase(TestCase):
    """Tests for the tokenization process"""

    def setUp(self):
        self.contact = Contact.objects.create(email='test@domain.com')

    def test_tokenize_untokenize(self):
        uidb36, token = tokenize(self.contact)
        self.assertEquals(untokenize(uidb36, token), self.contact)
        self.assertRaises(Http404, untokenize, 'toto', token)
        self.assertRaises(Http404, untokenize, uidb36, 'toto')


class MailerTestCase(TestCase):
    """Tests for the Mailer object"""

    def setUp(self):
        self.server = SMTPServer.objects.create(name='Test SMTP',
                                                host='smtp.domain.com',
                                                mails_hour=100)
        self.contacts = [Contact.objects.create(email='test1@domain.com'),
                         Contact.objects.create(email='test2@domain.com'),
                         Contact.objects.create(email='test3@domain.com'),
                         Contact.objects.create(email='test4@domain.com')]
        self.mailinglist = MailingList.objects.create(name='Test MailingList')
        self.mailinglist.subscribers.add(*self.contacts)
        self.newsletter = Newsletter.objects.create(title='Test Newsletter',
                                                    content='Test Newsletter Content',
                                                    slug='test-newsletter',
                                                    mailing_list=self.mailinglist,
                                                    server=self.server,
                                                    status=Newsletter.WAITING)
        self.newsletter.test_contacts.add(*self.contacts[:2])
        self.attachment = Attachment.objects.create(newsletter=self.newsletter,
                                                    title='Test attachment',
                                                    file_attachment=File(NamedTemporaryFile()))

    def test_expedition_list(self):
        mailer = Mailer(self.newsletter, test=True)
        self.assertEquals(len(mailer.expedition_list), 2)
        self.server.mails_hour = 1
        self.assertEquals(len(mailer.expedition_list), 1)

        self.server.mails_hour = 100
        mailer = Mailer(self.newsletter)
        self.assertEquals(len(mailer.expedition_list), 4)
        self.server.mails_hour = 3
        self.assertEquals(len(mailer.expedition_list), 3)

        self.server.mails_hour = 100
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.SENT)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[1],
                                            status=ContactMailingStatus.SENT)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[1],
                                            status=ContactMailingStatus.SENT)
        self.assertEquals(len(mailer.expedition_list), 2)
        self.assertFalse(self.contacts[0] in mailer.expedition_list)

    def test_can_send(self):
        mailer = Mailer(self.newsletter)
        self.assertTrue(mailer.can_send)

        # Checks credits
        self.server.mails_hour = 1
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.SENT)
        mailer = Mailer(self.newsletter)
        self.assertFalse(mailer.can_send)
        self.server.mails_hour = 10
        mailer = Mailer(self.newsletter)
        self.assertTrue(mailer.can_send)

        # Checks statut
        self.newsletter.status = Newsletter.DRAFT
        mailer = Mailer(self.newsletter)
        self.assertFalse(mailer.can_send)
        mailer = Mailer(self.newsletter, test=True)
        self.assertTrue(mailer.can_send)

        # Checks expedition time
        self.newsletter.status = Newsletter.WAITING
        self.newsletter.sending_date = datetime.now() + timedelta(hours=1)
        mailer = Mailer(self.newsletter)
        self.assertFalse(mailer.can_send)
        self.newsletter.sending_date = datetime.now()
        mailer = Mailer(self.newsletter)
        self.assertTrue(mailer.can_send)

    def test_run(self):
        mailer = Mailer(self.newsletter)
        mailer.smtp = FakeSMTP()
        mailer.run()
        self.assertEquals(mailer.smtp.mails_sent, 4)
        self.assertEquals(ContactMailingStatus.objects.filter(
            status=ContactMailingStatus.SENT, newsletter=self.newsletter).count(), 4)

        mailer = Mailer(self.newsletter, test=True)
        mailer.smtp = FakeSMTP()

        mailer.run()
        self.assertEquals(mailer.smtp.mails_sent, 2)
        self.assertEquals(ContactMailingStatus.objects.filter(
            status=ContactMailingStatus.SENT_TEST, newsletter=self.newsletter).count(), 2)

        mailer.smtp = None

    def test_update_newsletter_status(self):
        mailer = Mailer(self.newsletter, test=True)
        self.assertEquals(self.newsletter.status, Newsletter.WAITING)
        mailer.update_newsletter_status()
        self.assertEquals(self.newsletter.status, Newsletter.WAITING)

        mailer = Mailer(self.newsletter)
        self.assertEquals(self.newsletter.status, Newsletter.WAITING)
        mailer.update_newsletter_status()
        self.assertEquals(self.newsletter.status, Newsletter.SENDING)

        for contact in self.contacts:
            ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                                contact=contact,
                                                status=ContactMailingStatus.SENT)
        mailer.update_newsletter_status()
        self.assertEquals(self.newsletter.status, Newsletter.SENT)

    def test_update_newsletter_status_advanced(self):
        self.server.mails_hour = 2
        self.server.save()

        mailer = Mailer(self.newsletter)
        mailer.smtp = FakeSMTP()
        mailer.run()

        self.assertEquals(mailer.smtp.mails_sent, 2)
        self.assertEquals(ContactMailingStatus.objects.filter(
            status=ContactMailingStatus.SENT, newsletter=self.newsletter).count(), 2)
        self.assertEquals(self.newsletter.status, Newsletter.SENDING)

        self.server.mails_hour = 0
        self.server.save()

        mailer = Mailer(self.newsletter)
        mailer.smtp = FakeSMTP()
        mailer.run()

        self.assertEquals(mailer.smtp.mails_sent, 2)
        self.assertEquals(ContactMailingStatus.objects.filter(
            status=ContactMailingStatus.SENT, newsletter=self.newsletter).count(), 4)
        self.assertEquals(self.newsletter.status, Newsletter.SENT)

    def test_recipients_refused(self):
        server = SMTPServer.objects.create(name='Local SMTP',
                                           host='localhost')
        contact = Contact.objects.create(email='thisisaninvalidemail')
        self.newsletter.test_contacts.clear()
        self.newsletter.test_contacts.add(contact)
        self.newsletter.server = server
        self.newsletter.save()

        self.assertEquals(contact.valid, True)
        self.assertEquals(ContactMailingStatus.objects.filter(
            status=ContactMailingStatus.INVALID, newsletter=self.newsletter).count(), 0)

        mailer = Mailer(self.newsletter, test=True)
        mailer.run()

        self.assertEquals(Contact.objects.get(email='thisisaninvalidemail').valid, False)
        self.assertEquals(ContactMailingStatus.objects.filter(
            status=ContactMailingStatus.INVALID, newsletter=self.newsletter).count(), 1)


class StatisticsTestCase(TestCase):
    """Tests for the statistics functions"""

    def setUp(self):
        self.server = SMTPServer.objects.create(name='Test SMTP',
                                                host='smtp.domain.com')
        self.contacts = [Contact.objects.create(email='test1@domain.com'),
                         Contact.objects.create(email='test2@domain.com'),
                         Contact.objects.create(email='test3@domain.com'),
                         Contact.objects.create(email='test4@domain.com')]
        self.mailinglist = MailingList.objects.create(name='Test MailingList')
        self.mailinglist.subscribers.add(*self.contacts)
        self.newsletter = Newsletter.objects.create(title='Test Newsletter',
                                                    content='Test Newsletter Content',
                                                    mailing_list=self.mailinglist,
                                                    server=self.server,
                                                    status=Newsletter.SENT)
        self.links = [Link.objects.create(title='link 1', url='htt://link.1'),
                      Link.objects.create(title='link 2', url='htt://link.2')]

        for contact in self.contacts:
            ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                                contact=contact,
                                                status=ContactMailingStatus.SENT)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.SENT_TEST)

        self.recipients = len(self.contacts)
        self.status = ContactMailingStatus.objects.filter(newsletter=self.newsletter)

    def test_get_newsletter_opening_statistics(self):
        stats = get_newsletter_opening_statistics(self.status, self.recipients)
        self.assertEquals(stats['total_openings'], 0)
        self.assertEquals(stats['unique_openings'], 0)
        self.assertEquals(stats['double_openings'], 0)
        self.assertEquals(stats['unique_openings_percent'], 0)
        self.assertEquals(stats['unknow_openings'], 0)
        self.assertEquals(stats['unknow_openings_percent'], 0)
        self.assertEquals(stats['opening_average'], 0)

        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[1],
                                            status=ContactMailingStatus.OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[2],
                                            status=ContactMailingStatus.OPENED_ON_SITE)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[2],
                                            status=ContactMailingStatus.LINK_OPENED)
        status = ContactMailingStatus.objects.filter(newsletter=self.newsletter)

        stats = get_newsletter_opening_statistics(status, self.recipients)
        self.assertEquals(stats['total_openings'], 4)
        self.assertEquals(stats['unique_openings'], 3)
        self.assertEquals(stats['double_openings'], 1)
        self.assertEquals(stats['unique_openings_percent'], 75.0)
        self.assertEquals(stats['unknow_openings'], 1)
        self.assertEquals(stats['unknow_openings_percent'], 25.0)
        self.assertEquals(stats['opening_average'], 1.3333333333333333)
        self.assertEquals(stats['opening_deducted'], 0)

        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[3],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[3],
                                            status=ContactMailingStatus.LINK_OPENED)
        status = ContactMailingStatus.objects.filter(newsletter=self.newsletter)

        stats = get_newsletter_opening_statistics(status, self.recipients)
        self.assertEquals(stats['total_openings'], 5)
        self.assertEquals(stats['unique_openings'], 4)
        self.assertEquals(stats['double_openings'], 1)
        self.assertEquals(stats['unique_openings_percent'], 100.0)
        self.assertEquals(stats['unknow_openings'], 0)
        self.assertEquals(stats['unknow_openings_percent'], 0.0)
        self.assertEquals(stats['opening_average'], 1.25)
        self.assertEquals(stats['opening_deducted'], 1)

    def test_get_newsletter_on_site_opening_statistics(self):
        stats = get_newsletter_on_site_opening_statistics(self.status)
        self.assertEquals(stats['total_on_site_openings'], 0)
        self.assertEquals(stats['unique_on_site_openings'], 0)

        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.OPENED_ON_SITE)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.OPENED_ON_SITE)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[1],
                                            status=ContactMailingStatus.OPENED_ON_SITE)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[2],
                                            status=ContactMailingStatus.OPENED_ON_SITE)
        status = ContactMailingStatus.objects.filter(newsletter=self.newsletter)

        stats = get_newsletter_on_site_opening_statistics(status)
        self.assertEquals(stats['total_on_site_openings'], 4)
        self.assertEquals(stats['unique_on_site_openings'], 3)

    def test_get_newsletter_clicked_link_statistics(self):
        stats = get_newsletter_clicked_link_statistics(self.status, self.recipients, 0)
        self.assertEquals(stats['total_clicked_links'], 0)
        self.assertEquals(stats['total_clicked_links_percent'], 0)
        self.assertEquals(stats['double_clicked_links'], 0)
        self.assertEquals(stats['double_clicked_links_percent'], 0.0)
        self.assertEquals(stats['unique_clicked_links'], 0)
        self.assertEquals(stats['unique_clicked_links_percent'], 0)
        self.assertEquals(stats['clicked_links_by_openings'], 0.0)
        self.assertEquals(stats['clicked_links_average'], 0.0)

        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            link=self.links[0],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            link=self.links[1],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            link=self.links[1],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[1],
                                            link=self.links[0],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[2],
                                            link=self.links[0],
                                            status=ContactMailingStatus.LINK_OPENED)
        status = ContactMailingStatus.objects.filter(newsletter=self.newsletter)

        stats = get_newsletter_clicked_link_statistics(status, self.recipients, 3)
        self.assertEquals(stats['total_clicked_links'], 5)
        self.assertEquals(stats['total_clicked_links_percent'], 125.0)
        self.assertEquals(stats['double_clicked_links'], 2)
        self.assertEquals(stats['double_clicked_links_percent'], 50.0)
        self.assertEquals(stats['unique_clicked_links'], 3)
        self.assertEquals(stats['unique_clicked_links_percent'], 75.0)
        self.assertEquals(stats['clicked_links_by_openings'], 166.66666666666669)
        self.assertEquals(stats['clicked_links_average'], 1.6666666666666667)

    def test_get_newsletter_unsubscription_statistics(self):
        stats = get_newsletter_unsubscription_statistics(self.status, self.recipients)
        self.assertEquals(stats['total_unsubscriptions'], 0)
        self.assertEquals(stats['total_unsubscriptions_percent'], 0.0)

        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.UNSUBSCRIPTION)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[1],
                                            status=ContactMailingStatus.UNSUBSCRIPTION)

        status = ContactMailingStatus.objects.filter(newsletter=self.newsletter)

        stats = get_newsletter_unsubscription_statistics(status, self.recipients)
        self.assertEquals(stats['total_unsubscriptions'], 2)
        self.assertEquals(stats['total_unsubscriptions_percent'], 50.0)

    def test_get_newsletter_unsubscription_statistics_fix_doublon(self):
        stats = get_newsletter_unsubscription_statistics(self.status, self.recipients)
        self.assertEquals(stats['total_unsubscriptions'], 0)
        self.assertEquals(stats['total_unsubscriptions_percent'], 0.0)

        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.UNSUBSCRIPTION)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[1],
                                            status=ContactMailingStatus.UNSUBSCRIPTION)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[1],
                                            status=ContactMailingStatus.UNSUBSCRIPTION)

        status = ContactMailingStatus.objects.filter(newsletter=self.newsletter)

        stats = get_newsletter_unsubscription_statistics(status, self.recipients)
        self.assertEquals(stats['total_unsubscriptions'], 2)
        self.assertEquals(stats['total_unsubscriptions_percent'], 50.0)

    def test_get_newsletter_top_links(self):
        stats = get_newsletter_top_links(self.status)
        self.assertEquals(stats['top_links'], [])

        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            link=self.links[0],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            link=self.links[0],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            link=self.links[1],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[1],
                                            link=self.links[0],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[2],
                                            link=self.links[0],
                                            status=ContactMailingStatus.LINK_OPENED)
        status = ContactMailingStatus.objects.filter(newsletter=self.newsletter)

        stats = get_newsletter_top_links(status)
        self.assertEquals(len(stats['top_links']), 2)
        self.assertEquals(stats['top_links'][0]['link'], self.links[0])
        self.assertEquals(stats['top_links'][0]['total_clicks'], 4)
        self.assertEquals(stats['top_links'][0]['unique_clicks'], 3)
        self.assertEquals(stats['top_links'][1]['link'], self.links[1])
        self.assertEquals(stats['top_links'][1]['total_clicks'], 1)
        self.assertEquals(stats['top_links'][1]['unique_clicks'], 1)

    def test_get_newsletter_statistics(self):
        stats = get_newsletter_statistics(self.newsletter)

        self.assertEquals(stats['clicked_links_average'], 0.0)
        self.assertEquals(stats['clicked_links_by_openings'], 0.0)
        self.assertEquals(stats['double_clicked_links'], 0)
        self.assertEquals(stats['double_clicked_links_percent'], 00.0)
        self.assertEquals(stats['double_openings'], 0)
        self.assertEquals(stats['mails_sent'], 4)
        self.assertEquals(stats['mails_to_send'], 4)
        self.assertEquals(stats['opening_average'], 0)
        self.assertEquals(stats['remaining_mails'], 0)
        self.assertEquals(stats['tests_sent'], 1)
        self.assertEquals(stats['top_links'], [])
        self.assertEquals(stats['total_clicked_links'], 0)
        self.assertEquals(stats['total_clicked_links_percent'], 0.0)
        self.assertEquals(stats['total_on_site_openings'], 0)
        self.assertEquals(stats['total_openings'], 0)
        self.assertEquals(stats['total_unsubscriptions'], 0)
        self.assertEquals(stats['total_unsubscriptions_percent'], 0.0)
        self.assertEquals(stats['unique_clicked_links'], 0)
        self.assertEquals(stats['unique_clicked_links_percent'], 0.0)
        self.assertEquals(stats['unique_on_site_openings'], 0)
        self.assertEquals(stats['unique_openings'], 0)
        self.assertEquals(stats['unique_openings_percent'], 0)
        self.assertEquals(stats['unknow_openings'], 0)
        self.assertEquals(stats['unknow_openings_percent'], 0.0)

        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[1],
                                            status=ContactMailingStatus.OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.OPENED_ON_SITE)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[2],
                                            status=ContactMailingStatus.OPENED_ON_SITE)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            link=self.links[0],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            link=self.links[1],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            link=self.links[1],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[1],
                                            link=self.links[0],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[2],
                                            link=self.links[0],
                                            status=ContactMailingStatus.LINK_OPENED)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.UNSUBSCRIPTION)

        stats = get_newsletter_statistics(self.newsletter)

        self.assertEquals(stats['clicked_links_average'], 1.6666666666666667)
        self.assertEquals(stats['clicked_links_by_openings'], 100.0)
        self.assertEquals(stats['double_clicked_links'], 2)
        self.assertEquals(stats['double_clicked_links_percent'], 50.0)
        self.assertEquals(stats['double_openings'], 2)
        self.assertEquals(stats['mails_sent'], 4)
        self.assertEquals(stats['mails_to_send'], 4)
        self.assertEquals(stats['opening_average'], 1.6666666666666667)
        self.assertEquals(stats['remaining_mails'], 0)
        self.assertEquals(stats['tests_sent'], 1)
        self.assertEquals(stats['total_clicked_links'], 5)
        self.assertEquals(stats['total_clicked_links_percent'], 125.0)
        self.assertEquals(stats['total_on_site_openings'], 2)
        self.assertEquals(stats['total_openings'], 5)
        self.assertEquals(stats['total_unsubscriptions'], 1)
        self.assertEquals(stats['total_unsubscriptions_percent'], 25.0)
        self.assertEquals(stats['unique_clicked_links'], 3)
        self.assertEquals(stats['unique_clicked_links_percent'], 75.0)
        self.assertEquals(stats['unique_on_site_openings'], 2)
        self.assertEquals(stats['unique_openings'], 3)
        self.assertEquals(stats['unique_openings_percent'], 75)
        self.assertEquals(stats['unknow_openings'], 1)
        self.assertEquals(stats['unknow_openings_percent'], 25.0)

    def test_get_newsletter_statistics_division_by_zero(self):
        """Try to have a ZeroDivisionError by unsubscribing all contacts,
        and creating a ContactMailingStatus for more code coverage.
        Bug : http://github.com/Fantomas42/emencia-django-newsletter/issues#issue/9"""
        get_newsletter_statistics(self.newsletter)

        self.mailinglist.unsubscribers.add(*self.contacts)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.OPENED)
        get_newsletter_statistics(self.newsletter)


class NewsLetterRenderTest(TestCase):
    text = '''
<table style="width: 100%;" border="0" cellspacing="0" cellpadding="0" bgcolor="#eeeff1">
<tbody>
<tr>
<td>
<table style="width: 604px;" cellspacing="0" cellpadding="0" align="center" bgcolor="#FFFFFF ">
<tbody>
<tr>
<td bgcolor="#FFFFFF " width="600" height="88"><a href="http://hogrefe.it"><img src="http://www.hogrefe.it/media/upload/newsletter-1-registrati/1-news_02.jpg" border="0" alt="HOGREFE EDITORE" width="600" height="88" /></a></td>
</tr>
<tr>
<td style="text-align: right; pagging-bottom: 4px;"><a href="https://www.facebook.com/hogrefe.editore"><img src="http://www.hogrefe.it/media/upload/fb.png" border="0" alt="Facebook" width="25" height="25" /></a>&nbsp;<a href="http://www.linkedin.com/company/hogrefe-editore"><img src="http://www.hogrefe.it/media/upload/linkedin.png" border="0" alt="LinkedIn" width="25" height="25" /></a>&nbsp;<a href="http://www.youtube.com/user/HogrefeEditore"><img src="http://www.hogrefe.it/media/upload/youtube.png" border="0" alt="YouTube" width="25" height="25" /></a></td>
</tr>
<tr>
<td width="600" height="193"><img src="http://www.hogrefe.it/media/upload/img-nl-corsinovembre.png" border="0" alt="Due nuove iniziative formative organizzate da Hogrefe Editore" width="600" height="378" /></td>
</tr>
<tr>
<td style="font-family: Arial, Helvetica, sans-serif; color: #333333; font-size: 14px; line-height: 18px; text-align: justify; padding-top: 10px; padding-right: 30px; padding-bottom: 10px; padding-left: 30px;" colspan="2" bgcolor="#FFFFFF" width="560">
<table cellspacing="0" cellpadding="0">
<tbody>
<tr>
<td valign="top" width="130">&nbsp;</td>
<td width="20">&nbsp;</td>
<td style="font-size: 14px;" valign="top">&nbsp;</td>
</tr>
<tr>
<td valign="top" width="130"><img src="http://www.hogrefe.it/media/upload/lifedesign.png" border="0" alt="Life Design &amp; Career Counseling" width="130" height="140" /></td>
<td width="20">&nbsp;</td>
<td style="font-size: 14px;" valign="top"><span style="color: #000000;"><strong>Firenze, 29 e 30 novembre 2013</strong></span><br /><br /> <span style="color: #cc0000;"><strong>Life design e Career Counseling: la nuova visione dell'orientamento</strong></span><br /><br /> <span style="color: #000000;"><em>Sede: Fondazione dell'ordine degli Psicologi della Toscana, </em></span>Via Vasco de Gama n. 25 &bull; Firenze<br /><br /><span style="color: #000000;"><em>Docenti: Salvatore Soresi e Laura Nota</em></span><span style="color: #cc0000; font-size: 14px;"><span style="color: #cc0000; font-size: 14px;"></span></span><br /><br /><span style="color: #808080;">L&rsquo;approccio Life Design si propone di fornire gli strumenti per fronteggiare le sfide che sia chi si occupa di career counseling e vocational guidance sia le persone interessate alla loro scelta e progettazione professionale si trovano ad affrontare.<br /><span style="color: #cc0000;"><br /><span style="color: #cc0000;">Per maggiori informazioni e iscrizioni:<br /><a style="color: #cc0000;" href="http://www.fondazionepsicologi.it/images/brochure/life_design_15creditiECM.pdf">CLICCA QUI</a></span></span><br /></span></td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<table cellspacing="0" cellpadding="0">
<tbody>
<tr>
<td valign="top" width="130"><a href="http://www.hogrefe.it/it/catalogo/test/bambini-e-adolescenti/ados-2-autism-diagnostic-observation-schedule-second-edition/" target="_blank"><img style="border: 1px solid #cccccc;" src="http://www.hogrefe.it/media/upload/cover-ados2-web.png__128x0_q95_crop_upscale.png" border="0" alt="TDI Teate Depression Inventory" width="128" height="182" /></a></td>
<td width="20">&nbsp;</td>
<td style="font-size: 14px;" valign="top">
<div><span style="color: #000000; font-size: 14px;"><strong>Roma, 11 e 12 dicembre 2013<br /></strong></span><br /> <span style="color: #cc0000;"><strong>&ldquo;La Valutazione Diagnostica dell&rsquo;Autismo: i Moduli 1, 2, 3 e 4 di ADOS 2&rdquo;<br /><br /></strong> <span style="color: #000000;"><em>Sede: Istituto di Neuropsichiatria Infantile, Via dei Sabelli, 108 &bull; Roma<br /><br /> Docente: Dott.ssa Raffaella Faggioli.</em></span><br /><br /> <span style="color: #808080;">Il Corso ha lo scopo di promuovere le competenze in tema di diagnosi dell&rsquo;Autismo ed &egrave; rivolto a tutti gli operatori interessati ad acquisire uno strumento diagnostico riconosciuto e validato a livello internazionale ed aggiornato alle modifiche previste dal DSM5.</span><br /> <br /> <span style="color: #cc0000;">Per maggiori informazioni e iscrizioni:<br /><a style="color: #cc0000;" href="http://www.pediatrianpi.it/drupaluni/node/5640">CLICCA QUI</a><br /><br /></span></span></div>
</td>
</tr>
</tbody>
</table>
<div>
<h3 style="text-align: left;"><span style="color: #006cac;">I test di Hogrefe Editore: qualit&agrave; al servizio del professionista che vuole scegliere.</span></h3>
</div>
<p><span style="color: #888888;">Per maggiori informazioni:<br /></span><strong><a style="color: #888888;" href="mailto:info@hogrefe.it">info@hogrefe.it</a></strong><br /><strong><span style="color: #888888;">tel. +39 055 5320680</span></strong></p>
</td>
</tr>
<tr>
<td style="font-family: Arial, Helvetica, sans-serif; color: #ffffff; font-size: 12px; line-height: 18px; padding-top: 10px; padding-right: 30px; padding-bottom: 10px; padding-left: 30px;" align="justify" bgcolor="#787878">
<div>Hogrefe Editore Srl &bull; V.le A. Gramsci 42 &bull; 50132 Firenze &bull; Tel.: 055 5320680<br /> <a style="color: #ffffff;" href="mailto:info@hogrefe.it"><strong>info@hogrefe.it</strong></a> &bull; <a style="color: #ffffff;" href="http://www.hogrefe.it" target="_blank"><strong>www.hogrefe.it</strong></a> &bull; <a style="color: #ffffff;" href="http://qi.hogrefe.it/" target="_blank"><strong>qi.hogrefe.it</strong></a><br /> CF/P.IVA: 06267580485 &bull; REA: FI &ndash; 614260 &bull; Capitale sociale &euro; 10.000,00<br /> &copy; 2012 &bull; All Rights reserved</div>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>'''

    def setUp(self):
        title = 'Newsletter n. 39 - un nuovo corso ADOS-2 e il seminario life design'
        self.server = SMTPServer.objects.create(name='Test SMTP',
                                                host='smtp.domain.com')
        self.server_2 = SMTPServer.objects.create(name='Test SMTP 2',
                                                  host='smtp.domain2.com')
        self.contact = Contact.objects.create(email='scrivi@danielabaggiani.it',
                                              pk=3)
        self.mailinglist = MailingList.objects.create(name='prova iacopo')
        self.mailinglist.subscribers.add(self.contact)
        self.newsletter = Newsletter.objects.create(title=title,
                                                    content=self.text,
                                                    mailing_list=self.mailinglist,
                                                    server=self.server, slug=slugify(title))

    def test_track_links(self):
        uidb36, token = tokenize(self.contact)
        context = Context({'contact': "gino",
                           'domain': Site.objects.get_current().domain,
                           'newsletter': self.newsletter,
                           'tracking_image_format': 'jpg',
                           'uidb36': uidb36, 'token': token})
        rendered = track_links(self.text, context)
        print rendered