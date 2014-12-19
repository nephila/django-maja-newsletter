"""ModelAdmin for SMTPServer"""
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from maja_newsletter.models import SMTPServer, SendBatch


class SMTPServerAdminForm(forms.ModelForm):
    """Form ofr SMTPServer with custom validation"""

    def clean_headers(self):
        """Check if the headers are well formated"""
        for line in self.cleaned_data['headers'].splitlines():
            elems = line.split(':')
            if len(elems) < 2:
                raise ValidationError(_('Invalid syntax, do not forget the ":".'))
            if len(elems) > 2:
                raise ValidationError(_('Invalid syntax, several assignments by line.'))

        return self.cleaned_data['headers']

    class Meta:
        model = SMTPServer


class SendBatchInlineForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(SendBatchInlineForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['emails'].widget.attrs['readonly'] = 'readonly'

    class Meta:
        models = SendBatch


class SendBatchInline(admin.TabularInline):
    model = SendBatch
    can_delete = False
    extra = 1
    form = SendBatchInlineForm
    fields = ('emails', 'date_create', 'user')
    readonly_fields = ('date_create', 'user')


class SMTPServerAdmin(admin.ModelAdmin):
    form = SMTPServerAdminForm
    list_display = ('name', 'host', 'port', 'user', 'tls', 'mails_hour',)
    list_filter = ('tls',)
    search_fields = ('name', 'host', 'user')
    fieldsets = ((None, {'fields': ('name', )}),
                 (_('Configuration'), {'fields': ('host', 'port',
                                                  'user', 'password', 'tls')}),
                 (_('Miscellaneous'), {'fields': ('mails_hour', 'emails_remains','headers'),
                                       'classes': ('collapse', )}),
                 )
    actions = ['check_connections']
    readonly_fields = ('emails_remains', )
    inlines = (SendBatchInline,)

    def check_connections(self, request, queryset):
        """Check the SMTP connection"""
        message = '%s connection %s'
        for server in queryset:
            try:
                smtp = server.connect()
                if smtp:
                    status = 'OK'
                    smtp.quit()
                else:
                    status = 'KO'
            except:
                status = 'KO'
            self.message_user(request, message % (server.__unicode__(), status))
    check_connections.short_description = _('Check connection')

    def save_formset(self, request, form, formset, change):
        """
        Assign a default user to send batches when adding one
        """
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, SendBatch):
                if hasattr(instance, "user_id") and not instance.user_id:
                    instance.user = request.user
            instance.save()