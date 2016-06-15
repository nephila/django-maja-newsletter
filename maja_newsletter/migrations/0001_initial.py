# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-09 16:35
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import now

import maja_newsletter.models
import tagging.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '__latest__'),
        ('auth', '__latest__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('file_attachment', models.FileField(max_length=255, upload_to=maja_newsletter.models.get_newsletter_storage_path, verbose_name='file to attach')),
            ],
            options={
                'db_table': 'newsletter_attachment',
                'verbose_name': 'attachment',
                'verbose_name_plural': 'attachments',
            },
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=150, unique=True, verbose_name='email')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('subscriber', models.BooleanField(default=True, verbose_name='subscriber')),
                ('valid', models.BooleanField(default=True, verbose_name='valid email')),
                ('tester', models.BooleanField(default=False, verbose_name='contact tester')),
                ('tags', tagging.fields.TagField(blank=True, max_length=255, verbose_name='tags')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='creation date')),
                ('modification_date', models.DateTimeField(auto_now=True, verbose_name='modification date')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ('creation_date',),
                'db_table': 'newsletter_contact',
                'verbose_name': 'contact',
                'verbose_name_plural': 'contacts',
            },
        ),
        migrations.CreateModel(
            name='ContactMailingStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.IntegerField(choices=[(-1, 'sent in test'), (0, 'sent'), (1, 'error'), (2, 'invalid email'), (4, 'opened'), (5, 'opened on site'), (6, 'link opened'), (7, 'unsubscription')], verbose_name='status')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='creation date')),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maja_newsletter.Contact', verbose_name='contact')),
            ],
            options={
                'ordering': ('-creation_date',),
                'db_table': 'newsletter_contactmailingstatus',
                'verbose_name': 'contact mailing status',
                'verbose_name_plural': 'contact mailing statuses',
            },
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('url', models.CharField(max_length=255, verbose_name='url')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='creation date')),
            ],
            options={
                'ordering': ('-creation_date',),
                'db_table': 'newsletter_link',
                'verbose_name': 'link',
                'verbose_name_plural': 'links',
            },
        ),
        migrations.CreateModel(
            name='MailingList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='creation date')),
                ('modification_date', models.DateTimeField(auto_now=True, verbose_name='modification date')),
                ('subscribers', models.ManyToManyField(related_name='mailinglist_subscriber', to='maja_newsletter.Contact', verbose_name='subscribers')),
                ('unsubscribers', models.ManyToManyField(blank=True, null=True, related_name='mailinglist_unsubscriber', to='maja_newsletter.Contact', verbose_name='unsubscribers')),
            ],
            options={
                'ordering': ('-creation_date',),
                'db_table': 'newsletter_mailinglist',
                'verbose_name': 'mailing list',
                'verbose_name_plural': 'mailing lists',
            },
        ),
        migrations.CreateModel(
            name='Newsletter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='You can use the "{{ UNIQUE_KEY }}" variable for unique identifier within the newsletter\'s title.', max_length=255, verbose_name='title')),
                ('content', models.TextField(default='<body>\n<!-- Edit your newsletter here -->\n</body>', help_text='Or paste an URL.', verbose_name='content')),
                ('header_sender', models.CharField(default='Nephila <info@nephila.it>', max_length=255, verbose_name='sender')),
                ('header_reply', models.CharField(default='Nephila <info@nephila.it>', max_length=255, verbose_name='reply to')),
                ('status', models.IntegerField(choices=[(0, 'draft'), (1, 'waiting sending'), (2, 'sending'), (4, 'sent'), (5, 'canceled')], default=0, verbose_name='status')),
                ('sending_date', models.DateTimeField(default=now, verbose_name='sending date')),
                ('slug', models.SlugField(help_text='Used for displaying the newsletter on the site.', max_length=255, unique=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='creation date')),
                ('modification_date', models.DateTimeField(auto_now=True, verbose_name='modification date')),
                ('mailing_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maja_newsletter.MailingList', verbose_name='mailing list')),
            ],
            options={
                'ordering': ('-creation_date',),
                'db_table': 'newsletter_newsletter',
                'verbose_name': 'newsletter',
                'verbose_name_plural': 'newsletters',
                'permissions': (('can_change_status', 'Can change status'),),
            },
        ),
        migrations.CreateModel(
            name='SendBatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('emails', models.IntegerField(verbose_name='emails batch')),
                ('date_create', models.DateTimeField(auto_now_add=True, verbose_name='add date')),
            ],
            options={
                'db_table': 'newsletter_sendbatch',
                'verbose_name': 'email batch',
                'verbose_name_plural': 'email batches',
            },
        ),
        migrations.CreateModel(
            name='SMTPServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('host', models.CharField(max_length=255, verbose_name='server host')),
                ('user', models.CharField(blank=True, help_text='Leave empty if the host is public.', max_length=128, verbose_name='server user')),
                ('password', models.CharField(blank=True, help_text='Leave empty if the host is public.', max_length=128, verbose_name='server password')),
                ('port', models.IntegerField(default=25, verbose_name='server port')),
                ('tls', models.BooleanField(default=False, verbose_name='server use TLS')),
                ('headers', models.TextField(blank=True, help_text='key1: value1 key2: value2, splitted by return line.\nUseful for passing some tracking headers if your provider allows it.', verbose_name='custom headers')),
                ('mails_hour', models.IntegerField(default=0, help_text='E-Mail sending rate in messages per hour', verbose_name='e-mail send rate')),
                ('emails_remains', models.IntegerField(default=10000, help_text='Sendable E-Mail in the current account', verbose_name='remaining e-mail')),
            ],
            options={
                'db_table': 'newsletter_smtpserver',
                'verbose_name': 'SMTP server',
                'verbose_name_plural': 'SMTP servers',
            },
        ),
        migrations.CreateModel(
            name='WorkGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('contacts', models.ManyToManyField(blank=True, null=True, to='maja_newsletter.Contact', verbose_name='contacts')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.Group', verbose_name='permissions group')),
                ('mailinglists', models.ManyToManyField(blank=True, null=True, to='maja_newsletter.MailingList', verbose_name='mailing lists')),
                ('newsletters', models.ManyToManyField(blank=True, null=True, to='maja_newsletter.Newsletter', verbose_name='newsletters')),
            ],
            options={
                'db_table': 'newsletter_workgroup',
                'verbose_name': 'workgroup',
                'verbose_name_plural': 'workgroups',
            },
        ),
        migrations.AddField(
            model_name='sendbatch',
            name='server',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maja_newsletter.SMTPServer'),
        ),
        migrations.AddField(
            model_name='sendbatch',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='operator'),
        ),
        migrations.AddField(
            model_name='newsletter',
            name='server',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='maja_newsletter.SMTPServer', verbose_name='smtp server'),
        ),
        migrations.AddField(
            model_name='newsletter',
            name='test_contacts',
            field=models.ManyToManyField(blank=True, null=True, to='maja_newsletter.Contact', verbose_name='test contacts'),
        ),
        migrations.AddField(
            model_name='contactmailingstatus',
            name='link',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='maja_newsletter.Link', verbose_name='link'),
        ),
        migrations.AddField(
            model_name='contactmailingstatus',
            name='newsletter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maja_newsletter.Newsletter', verbose_name='newsletter'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='newsletter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maja_newsletter.Newsletter', verbose_name='newsletter'),
        ),
    ]
