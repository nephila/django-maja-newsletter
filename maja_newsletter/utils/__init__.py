"""Utils for maja_newsletter"""
from distutils.version import LooseVersion

import django
from django.template import Context, Template

DJANGO_1_4 = LooseVersion(django.get_version()) < LooseVersion('1.5')
DJANGO_1_5 = LooseVersion(django.get_version()) < LooseVersion('1.6')
DJANGO_1_6 = LooseVersion(django.get_version()) < LooseVersion('1.7')
DJANGO_1_7 = LooseVersion(django.get_version()) < LooseVersion('1.8')
DJANGO_1_8 = LooseVersion(django.get_version()) < LooseVersion('1.9')
DJANGO_1_9 = LooseVersion(django.get_version()) < LooseVersion('1.10')
DJANGO_1_10 = LooseVersion(django.get_version()) < LooseVersion('1.11')


def render_string(template_string, context={}):
    """Shortcut for render a template string with a context"""
    t = Template(template_string)
    c = Context(context)
    return t.render(c)


def wrap_transaction(*args, **kwargs):
    """
    This is a simple  decorator that wraps
    transaction.commit_on_success / atomic decorators.
    While the two are not equivalent, they can be regarded as equal for the
    use in the cms codebase.
    """
    from django.db import transaction
    try:
        from django.db.transaction import atomic  # nopyflakes
        return transaction.atomic(*args, **kwargs)
    except ImportError:
        return transaction.commit_on_success(*args, **kwargs)