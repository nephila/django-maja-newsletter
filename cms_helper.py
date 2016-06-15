#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

HELPER_SETTINGS = dict(
    ROOT_URLCONF='maja_newsletter.urls',
    INSTALLED_APPS=[
        'tagging',
        'maja_newsletter',
    ],
    NEWSLETTER_SLEEP_BETWEEN_SENDING=False,
    SOUTH_TESTS_MIGRATE=False,
)


def run():
    from djangocms_helper import runner
    runner.run('maja_newsletter')


def setup():
    import sys
    from djangocms_helper import runner
    runner.setup('maja_newsletter', sys.modules[__name__])

if __name__ == '__main__':
    run()
