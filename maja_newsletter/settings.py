"""Settings for maja_newsletter"""
import string
from django.conf import settings

BASE64_IMAGES = {
    'gif': 'AJEAAAAAAP///////wAAACH5BAEHAAIALAAAAAABAAEAAAICVAEAOw==',
    'png': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAABBJREFUeNpi+P//PwNAgAEACPwC/tuiTRYAAAAASUVORK5CYII=',
    'jpg': '/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAYEBAQFBAYFBQYJBgUGCQsIBgYICwwKCgsKCgwQDAwMDAwMEAwODxAPDgwTExQUExMcGxsbHCAgICAgICAgICD/2wBDAQcHBw0MDRgQEBgaFREVGiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICD/wAARCAABAAEDAREAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACP/EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AVIP/2Q=='
    }

USE_WORKGROUPS = getattr(settings, 'NEWSLETTER_USE_WORKGROUPS', False)
USE_UTM_TAGS = getattr(settings, 'NEWSLETTER_USE_UTM_TAGS', True)
USE_TINYMCE = getattr(settings, 'NEWSLETTER_USE_TINYMCE',
                      'tinymce' in settings.INSTALLED_APPS)
USE_CKEDITOR = getattr(settings, 'NEWSLETTER_USE_CKEDITOR',
                      'djangocms_text_ckeditor' in settings.INSTALLED_APPS)

USE_PRETTIFY = getattr(settings, 'NEWSLETTER_USE_PRETTIFY', False)
USE_PREMAILER = getattr(settings, 'NEWSLETTER_USE_PREMAILER', True)


MAILER_HARD_LIMIT = getattr(settings, 'NEWSLETTER_MAILER_HARD_LIMIT', 10000)

INCLUDE_UNSUBSCRIPTION = getattr(settings, 'NEWSLETTER_INCLUDE_UNSUBSCRIPTION', True)

UNSUBSCRIBE_ALL = getattr(settings, 'NEWSLETTER_UNSUBSCRIBE_ALL', False)

UNIQUE_KEY_LENGTH = getattr(settings, 'NEWSLETTER_UNIQUE_KEY_LENGTH', 8)
UNIQUE_KEY_CHAR_SET = getattr(settings, 'NEWSLETTER_UNIQUE_KEY_CHAR_SET', string.ascii_uppercase + string.digits)

DEFAULT_HEADER_SENDER = getattr(
    settings, 'NEWSLETTER_DEFAULT_HEADER_SENDER', 'Maja Newsletter<noreply@example.com>'
)
DEFAULT_HEADER_REPLY = getattr(
    settings, 'NEWSLETTER_DEFAULT_HEADER_REPLY', DEFAULT_HEADER_SENDER
)

TRACKING_LINKS = getattr(settings, 'NEWSLETTER_TRACKING_LINKS', True)
TRACKING_IMAGE_FORMAT = getattr(settings, 'NEWSLETTER_TRACKING_IMAGE_FORMAT', 'jpg')
TRACKING_IMAGE = getattr(
    settings, 'NEWSLETTER_TRACKING_IMAGE', BASE64_IMAGES[TRACKING_IMAGE_FORMAT]
)

MAILINGLIST_DELETE_THRESHOLD = getattr(
    settings, 'NEWSLETTER_MAILINGLIST_DELETE_THRESHOLD', 5000
)
MAILINGLIST_DELETE_SAFE = getattr(
    settings, 'NEWSLETTER_MAILINGLIST_DELETE_SAFE', False
)

SLEEP_BETWEEN_SENDING = getattr(settings, 'NEWSLETTER_SLEEP_BETWEEN_SENDING', True)
RESTART_CONNECTION_BETWEEN_SENDING = getattr(
    settings, 'NEWSLETTER_RESTART_CONNECTION_BETWEEN_SENDING', False
)

BASE_PATH = getattr(settings, 'NEWSLETTER_BASE_PATH', 'upload/newsletter')
VERBOSE_MAILER = getattr(settings, 'NEWSLETTER_VERBOSE_MAILER', False)

# NPH
# Relative to MEDIA_ROOT
FILEBROWSER_DIRECTORY = getattr(settings, 'FILEBROWSER_DIRECTORY', 'upload/')
NEWSLETTER_TINYMCE_TEMPLATE_DIR = getattr(settings, 'NEWSLETTER_TINYMCE_TEMPLATE_DIR', 'upload/tinymce/templates/')
NEWSLETTER_TINYMCE_TEMPLATE_URL = getattr(settings, 'NEWSLETTER_TINYMCE_TEMPLATE_URL', '/tinymce/templates/')
CKEDITOR_SETTINGS = getattr(settings, 'NEWSLETTER_CKEDITOR_SETTINGS', getattr(settings, 'CKEDITOR_SETTINGS', {}))

USE_CELERY = getattr(settings, 'NEWSLETTER_USE_CELERY', False)

EXPORT_FILE_NAME = getattr(settings, 'NEWSLETTER_EXPORT_FILE_NAME', 'exported_contacts')
EXPORT_EMAIL_SUBJECT = getattr(settings, 'NEWSLETTER_EXPORT_EMAIL_SUBJECT', 'exported_contacts')