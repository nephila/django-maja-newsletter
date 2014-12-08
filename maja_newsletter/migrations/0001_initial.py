from south.db import db
from django.db import models
from maja_newsletter.models import *


class Migration:

    def forwards(self, orm):

        # Adding model 'MailingList'
        db.create_table('newsletter_mailinglist', (
            ('id', orm['maja_newsletter.MailingList:id']),
            ('name', orm['maja_newsletter.MailingList:name']),
            ('description', orm['maja_newsletter.MailingList:description']),
            ('creation_date', orm['maja_newsletter.MailingList:creation_date']),
            ('modification_date', orm['maja_newsletter.MailingList:modification_date']),
        ))
        db.send_create_signal('maja_newsletter', ['MailingList'])

        # Adding model 'ContactMailingStatus'
        db.create_table('newsletter_contactmailingstatus', (
            ('id', orm['maja_newsletter.ContactMailingStatus:id']),
            ('newsletter', orm['maja_newsletter.ContactMailingStatus:newsletter']),
            ('contact', orm['maja_newsletter.ContactMailingStatus:contact']),
            ('status', orm['maja_newsletter.ContactMailingStatus:status']),
            ('link', orm['maja_newsletter.ContactMailingStatus:link']),
            ('creation_date', orm['maja_newsletter.ContactMailingStatus:creation_date']),
        ))
        db.send_create_signal('maja_newsletter', ['ContactMailingStatus'])

        # Adding model 'WorkGroup'
        db.create_table('newsletter_workgroup', (
            ('id', orm['maja_newsletter.WorkGroup:id']),
            ('name', orm['maja_newsletter.WorkGroup:name']),
            ('group', orm['maja_newsletter.WorkGroup:group']),
        ))
        db.send_create_signal('maja_newsletter', ['WorkGroup'])

        # Adding model 'Link'
        db.create_table('newsletter_link', (
            ('id', orm['maja_newsletter.Link:id']),
            ('title', orm['maja_newsletter.Link:title']),
            ('url', orm['maja_newsletter.Link:url']),
            ('creation_date', orm['maja_newsletter.Link:creation_date']),
        ))
        db.send_create_signal('maja_newsletter', ['Link'])

        # Adding model 'Newsletter'
        db.create_table('newsletter_newsletter', (
            ('id', orm['maja_newsletter.Newsletter:id']),
            ('title', orm['maja_newsletter.Newsletter:title']),
            ('content', orm['maja_newsletter.Newsletter:content']),
            ('mailing_list', orm['maja_newsletter.Newsletter:mailing_list']),
            ('server', orm['maja_newsletter.Newsletter:server']),
            ('header_sender', orm['maja_newsletter.Newsletter:header_sender']),
            ('header_reply', orm['maja_newsletter.Newsletter:header_reply']),
            ('status', orm['maja_newsletter.Newsletter:status']),
            ('sending_date', orm['maja_newsletter.Newsletter:sending_date']),
            ('slug', orm['maja_newsletter.Newsletter:slug']),
            ('creation_date', orm['maja_newsletter.Newsletter:creation_date']),
            ('modification_date', orm['maja_newsletter.Newsletter:modification_date']),
        ))
        db.send_create_signal('maja_newsletter', ['Newsletter'])

        # Adding model 'SMTPServer'
        db.create_table('newsletter_smtpserver', (
            ('id', orm['maja_newsletter.SMTPServer:id']),
            ('name', orm['maja_newsletter.SMTPServer:name']),
            ('host', orm['maja_newsletter.SMTPServer:host']),
            ('user', orm['maja_newsletter.SMTPServer:user']),
            ('password', orm['maja_newsletter.SMTPServer:password']),
            ('port', orm['maja_newsletter.SMTPServer:port']),
            ('tls', orm['maja_newsletter.SMTPServer:tls']),
            ('headers', orm['maja_newsletter.SMTPServer:headers']),
            ('mails_hour', orm['maja_newsletter.SMTPServer:mails_hour']),
        ))
        db.send_create_signal('maja_newsletter', ['SMTPServer'])

        # Adding model 'Contact'
        db.create_table('newsletter_contact', (
            ('id', orm['maja_newsletter.Contact:id']),
            ('email', orm['maja_newsletter.Contact:email']),
            ('first_name', orm['maja_newsletter.Contact:first_name']),
            ('last_name', orm['maja_newsletter.Contact:last_name']),
            ('subscriber', orm['maja_newsletter.Contact:subscriber']),
            ('valid', orm['maja_newsletter.Contact:valid']),
            ('tester', orm['maja_newsletter.Contact:tester']),
            ('tags', orm['maja_newsletter.Contact:tags']),
            ('content_type', orm['maja_newsletter.Contact:content_type']),
            ('object_id', orm['maja_newsletter.Contact:object_id']),
            ('creation_date', orm['maja_newsletter.Contact:creation_date']),
            ('modification_date', orm['maja_newsletter.Contact:modification_date']),
        ))
        db.send_create_signal('maja_newsletter', ['Contact'])

        # Adding ManyToManyField 'WorkGroup.mailinglists'
        db.create_table('newsletter_workgroup_mailinglists', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('workgroup', models.ForeignKey(orm.WorkGroup, null=False)),
            ('mailinglist', models.ForeignKey(orm.MailingList, null=False))
        ))

        # Adding ManyToManyField 'MailingList.subscribers'
        db.create_table('newsletter_mailinglist_subscribers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mailinglist', models.ForeignKey(orm.MailingList, null=False)),
            ('contact', models.ForeignKey(orm.Contact, null=False))
        ))

        # Adding ManyToManyField 'WorkGroup.contacts'
        db.create_table('newsletter_workgroup_contacts', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('workgroup', models.ForeignKey(orm.WorkGroup, null=False)),
            ('contact', models.ForeignKey(orm.Contact, null=False))
        ))

        # Adding ManyToManyField 'WorkGroup.newsletters'
        db.create_table('newsletter_workgroup_newsletters', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('workgroup', models.ForeignKey(orm.WorkGroup, null=False)),
            ('newsletter', models.ForeignKey(orm.Newsletter, null=False))
        ))

        # Adding ManyToManyField 'MailingList.unsubscribers'
        db.create_table('newsletter_mailinglist_unsubscribers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mailinglist', models.ForeignKey(orm.MailingList, null=False)),
            ('contact', models.ForeignKey(orm.Contact, null=False))
        ))

        # Adding ManyToManyField 'Newsletter.test_contacts'
        db.create_table('newsletter_newsletter_test_contacts', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('newsletter', models.ForeignKey(orm.Newsletter, null=False)),
            ('contact', models.ForeignKey(orm.Contact, null=False))
        ))

    def backwards(self, orm):

        # Deleting model 'MailingList'
        db.delete_table('newsletter_mailinglist')

        # Deleting model 'ContactMailingStatus'
        db.delete_table('newsletter_contactmailingstatus')

        # Deleting model 'WorkGroup'
        db.delete_table('newsletter_workgroup')

        # Deleting model 'Link'
        db.delete_table('newsletter_link')

        # Deleting model 'Newsletter'
        db.delete_table('newsletter_newsletter')

        # Deleting model 'SMTPServer'
        db.delete_table('newsletter_smtpserver')

        # Deleting model 'Contact'
        db.delete_table('newsletter_contact')

        # Dropping ManyToManyField 'WorkGroup.mailinglists'
        db.delete_table('newsletter_workgroup_mailinglists')

        # Dropping ManyToManyField 'MailingList.subscribers'
        db.delete_table('newsletter_mailinglist_subscribers')

        # Dropping ManyToManyField 'WorkGroup.contacts'
        db.delete_table('newsletter_workgroup_contacts')

        # Dropping ManyToManyField 'WorkGroup.newsletters'
        db.delete_table('newsletter_workgroup_newsletters')

        # Dropping ManyToManyField 'MailingList.unsubscribers'
        db.delete_table('newsletter_mailinglist_unsubscribers')

        # Dropping ManyToManyField 'Newsletter.test_contacts'
        db.delete_table('newsletter_newsletter_test_contacts')

    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'maja_newsletter.attachment': {
            'Meta': {'object_name': 'Attachment', 'db_table': "'newsletter_attachment'"},
            'file_attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'newsletter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['maja_newsletter.Newsletter']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'maja_newsletter.contact': {
            'Meta': {'ordering': "('creation_date',)", 'object_name': 'Contact', 'db_table': "'newsletter_contact'"},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '150'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'modification_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'subscriber': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'tags': ('tagging.fields.TagField', [], {}),
            'tester': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'valid': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'maja_newsletter.contactmailingstatus': {
            'Meta': {'ordering': "('-creation_date',)", 'object_name': 'ContactMailingStatus', 'db_table': "'newsletter_contactmailingstatus'"},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['maja_newsletter.Contact']"}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['maja_newsletter.Link']", 'null': 'True', 'blank': 'True'}),
            'newsletter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['maja_newsletter.Newsletter']"}),
            'status': ('django.db.models.fields.IntegerField', [], {})
        },
        'maja_newsletter.link': {
            'Meta': {'ordering': "('-creation_date',)", 'object_name': 'Link', 'db_table': "'newsletter_link'"},
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'maja_newsletter.mailinglist': {
            'Meta': {'ordering': "('-creation_date',)", 'object_name': 'MailingList', 'db_table': "'newsletter_mailinglist'"},
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modification_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'subscribers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'mailinglist_subscriber'", 'symmetrical': 'False', 'to': "orm['maja_newsletter.Contact']"}),
            'unsubscribers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'mailinglist_unsubscriber'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['maja_newsletter.Contact']"})
        },
        'maja_newsletter.newsletter': {
            'Meta': {'ordering': "('-creation_date',)", 'object_name': 'Newsletter', 'db_table': "'newsletter_newsletter'"},
            'content': ('django.db.models.fields.TextField', [], {'default': "u'<body>\\n<!-- Edit your newsletter here -->\\n</body>'"}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'header_reply': ('django.db.models.fields.CharField', [], {'default': "'Hogrefe Editore  <info@hogrefe.it>'", 'max_length': '255'}),
            'header_sender': ('django.db.models.fields.CharField', [], {'default': "'Hogrefe Editore  <info@hogrefe.it>'", 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailing_list': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['maja_newsletter.MailingList']"}),
            'modification_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'sending_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'server': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'to': "orm['maja_newsletter.SMTPServer']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'test_contacts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['maja_newsletter.Contact']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'maja_newsletter.smtpserver': {
            'Meta': {'object_name': 'SMTPServer', 'db_table': "'newsletter_smtpserver'"},
            'emails_remains': ('django.db.models.fields.IntegerField', [], {'default': '10000'}),
            'headers': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'host': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mails_hour': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'port': ('django.db.models.fields.IntegerField', [], {'default': '25'}),
            'tls': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        'maja_newsletter.workgroup': {
            'Meta': {'object_name': 'WorkGroup', 'db_table': "'newsletter_workgroup'"},
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['maja_newsletter.Contact']", 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailinglists': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['maja_newsletter.MailingList']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'newsletters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['maja_newsletter.Newsletter']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['maja_newsletter']