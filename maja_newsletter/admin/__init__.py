"""Admin for maja_newsletter"""
from django.contrib import admin
from django.conf import settings

from maja_newsletter.models import Link
from maja_newsletter.models import Contact
from maja_newsletter.models import WorkGroup
from maja_newsletter.models import SMTPServer
from maja_newsletter.models import Newsletter
from maja_newsletter.models import MailingList
from maja_newsletter.models import ContactMailingStatus

from maja_newsletter.settings import USE_WORKGROUPS
from maja_newsletter.admin.contact import ContactAdmin
from maja_newsletter.admin.workgroup import WorkGroupAdmin
from maja_newsletter.admin.newsletter import NewsletterAdmin
from maja_newsletter.admin.smtpserver import SMTPServerAdmin
from maja_newsletter.admin.mailinglist import MailingListAdmin


admin.site.register(Contact, ContactAdmin)
admin.site.register(SMTPServer, SMTPServerAdmin)
admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(MailingList, MailingListAdmin)

if USE_WORKGROUPS:
    admin.site.register(WorkGroup, WorkGroupAdmin)


class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'creation_date')

if settings.DEBUG:
    admin.site.register(Link, LinkAdmin)
    admin.site.register(ContactMailingStatus)
