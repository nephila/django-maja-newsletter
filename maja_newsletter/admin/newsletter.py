"""ModelAdmin for Newsletter"""
from HTMLParser import HTMLParseError

from django import forms
from django.db import models
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from maja_newsletter.models import Contact
from maja_newsletter.models import Newsletter
from maja_newsletter.models import Attachment
from maja_newsletter.models import MailingList
from maja_newsletter.mailer import Mailer
from maja_newsletter.settings import USE_TINYMCE
from maja_newsletter.settings import USE_CELERY
from maja_newsletter.settings import USE_WORKGROUPS
from maja_newsletter.settings import USE_CKEDITOR
try:
    CAN_USE_PREMAILER = True
    from maja_newsletter.utils.premailer_old import Premailer
    from maja_newsletter.utils.premailer_old import PremailerError
except ImportError:
    CAN_USE_PREMAILER = False
from maja_newsletter.utils.workgroups import request_workgroups
from maja_newsletter.utils.workgroups import request_workgroups_contacts_pk
from maja_newsletter.utils.workgroups import request_workgroups_newsletters_pk
from maja_newsletter.utils.workgroups import request_workgroups_mailinglists_pk

from ..tasks import celery_send_newsletter

class AttachmentAdminInline(admin.TabularInline):
    model = Attachment
    extra = 1
    fieldsets = ((None, {'fields': (('title', 'file_attachment'))}),)


class BaseNewsletterAdmin(admin.ModelAdmin):
    date_hierarchy = 'creation_date'
    list_display = ('title', 'mailing_list', 'server', 'status',
                    'sending_date', 'creation_date', 'modification_date',
                    'historic_link', 'statistics_link')
    list_filter = ('status', 'sending_date', 'creation_date', 'modification_date')
    search_fields = ('title', 'content', 'header_sender', 'header_reply')
    filter_horizontal = ['test_contacts']
    fieldsets = ((None, {'fields': ('title', 'content',)}),
                 (_('Receivers'), {'fields': ('mailing_list', 'test_contacts',)}),
                 (_('Sending'), {'fields': ('sending_date',)}),
                 (_('Miscellaneous'), {'fields': ('server', 'header_sender',
                                                  'header_reply', 'slug'),
                                       'classes': ('collapse',)}),
                 )
    prepopulated_fields = {'slug': ('title',)}
    inlines = (AttachmentAdminInline,)
    actions = ['send_mail_test', 'make_ready_to_send', 'make_cancel_sending']
    actions_on_top = False
    actions_on_bottom = True

    def get_actions(self, request):
        actions = super(BaseNewsletterAdmin, self).get_actions(request)
        if not request.user.has_perm('newsletter.can_change_status'):
            del actions['make_ready_to_send']
            del actions['make_cancel_sending']
        return actions

    def queryset(self, request):
        queryset = super(BaseNewsletterAdmin, self).queryset(request)
        if not request.user.is_superuser and USE_WORKGROUPS:
            newsletters_pk = request_workgroups_newsletters_pk(request)
            queryset = queryset.filter(pk__in=newsletters_pk)
        return queryset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'mailing_list' and \
               not request.user.is_superuser and USE_WORKGROUPS:
            mailinglists_pk = request_workgroups_mailinglists_pk(request)
            kwargs['queryset'] = MailingList.objects.filter(pk__in=mailinglists_pk)
            return db_field.formfield(**kwargs)
        return super(BaseNewsletterAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'status' and \
               not request.user.has_perm('newsletter.can_change_status'):
            kwargs['choices'] = ((Newsletter.DRAFT, _('Default')),)
            return db_field.formfield(**kwargs)
        return super(BaseNewsletterAdmin, self).formfield_for_choice_field(
            db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'test_contacts':
            queryset = Contact.objects.filter(tester=True)
            if not request.user.is_superuser and USE_WORKGROUPS:
                contacts_pk = request_workgroups_contacts_pk(request)
                queryset = queryset.filter(pk__in=contacts_pk)
            kwargs['queryset'] = queryset
        return super(BaseNewsletterAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs)

    def save_model(self, request, newsletter, form, change):
        workgroups = []
        if not newsletter.pk and not request.user.is_superuser \
               and USE_WORKGROUPS:
            workgroups = request_workgroups(request)

        if newsletter.content.startswith('http://'):
            if CAN_USE_PREMAILER:
                try:
                    premailer = Premailer(newsletter.content.strip())
                    newsletter.content = premailer.transform()
                except PremailerError:
                    self.message_user(request, _('Unable to download HTML, due to errors within.'))
            else:
                self.message_user(request, _('Please install lxml for parsing an URL.'))
        if not request.user.has_perm('newsletter.can_change_status'):
            newsletter.status = form.initial.get('status', Newsletter.DRAFT)

        newsletter.save()

        for workgroup in workgroups:
            workgroup.newsletters.add(newsletter)

    def historic_link(self, newsletter):
        """Display link for historic"""
        if newsletter.contactmailingstatus_set.count():
            return u'<a href="%s">%s</a>' % (newsletter.get_historic_url(), _('View historic'))
        return _('Not available')
    historic_link.allow_tags = True
    historic_link.short_description = _('Historic')

    def statistics_link(self, newsletter):
        """Display link for statistics"""
        if newsletter.status == Newsletter.SENDING or \
           newsletter.status == Newsletter.SENT:
            return u'<a href="%s">%s</a>' % (newsletter.get_statistics_url(), _('View statistics'))
        return _('Not available')
    statistics_link.allow_tags = True
    statistics_link.short_description = _('Statistics')

    def send_mail_test(self, request, queryset):
        """Send newsletter in test"""
        for newsletter in queryset:
            if newsletter.test_contacts.count():
                mailer = Mailer(newsletter, test=True)
                try:
                    mailer.run()
                except HTMLParseError:
                    self.message_user(request, _('Unable send newsletter, due to errors within HTML.'))
                    continue
                self.message_user(request, _('%s succesfully sent.') % newsletter)
            else:
                self.message_user(request, _('No test contacts assigned for %s.') % newsletter)
    send_mail_test.short_description = _('Send test email')

    def make_ready_to_send(self, request, queryset):
        """Make newsletter ready to send"""
        from django.contrib import messages
        queryset = queryset.filter(status=Newsletter.DRAFT)
        emails_to_send = 0
        sent_all = True
        for newsletter in queryset:
            emails_to_send += len(newsletter.mailing_list.expedition_set())
            if emails_to_send > newsletter.server.emails_remains:
                messages.warning(request, _('You do not have enough e-mail'))
                sent_all = False
                break
            newsletter.status = Newsletter.WAITING
            newsletter.server.emails_remains = newsletter.server.emails_remains - emails_to_send
            newsletter.server.save()
            newsletter.save()
            if USE_CELERY:
                celery_send_newsletter.delay(newsletter)
        if sent_all:
            messages.success(request, _('%s newletters are ready to send') % queryset.count())
        # self.message_user(request, message)
    make_ready_to_send.short_description = _('Make ready to send')

    def make_cancel_sending(self, request, queryset):
        """Cancel the sending of newsletters"""
        queryset = queryset.filter(models.Q(status=Newsletter.WAITING) |
                                   models.Q(status=Newsletter.SENDING))
        for newsletter in queryset:
            newsletter.status = Newsletter.CANCELED
            newsletter.save()
        self.message_user(request, _('%s newletters are cancelled') % queryset.count())
    make_cancel_sending.short_description = _('Cancel the sending')


if USE_TINYMCE:
    from tinymce.widgets import TinyMCE

    class NewsletterTinyMCEForm(forms.ModelForm):
        content = forms.CharField(
            widget=TinyMCE(attrs={'cols': 150, 'rows': 80}))

        class Meta:
            model = Newsletter

    class NewsletterAdmin(BaseNewsletterAdmin):
        form = NewsletterTinyMCEForm
elif USE_CKEDITOR:
    from djangocms_text_ckeditor.widgets import TextEditorWidget

    class NewsletterAdmin(BaseNewsletterAdmin):
        formfield_overrides = {
            models.TextField: {'widget': TextEditorWidget(configuration='NEWSLETTER_CKEDITOR_SETTINGS')}
        }
else:
    class NewsletterAdmin(BaseNewsletterAdmin):
        pass
