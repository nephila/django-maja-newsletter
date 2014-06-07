#!/usr/bin/env python
from __future__ import with_statement
from contextlib import contextmanager
import os
import shutil
import sys
from tempfile import mkdtemp
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

os.environ['DJANGO_SETTINGS_MODULE'] = "maja_newsletter.testsettings"

@contextmanager
def temp_dir():
    name = mkdtemp()
    yield name
    shutil.rmtree(name)

def main():
    with temp_dir() as STATIC_ROOT:
        with temp_dir() as MEDIA_ROOT:
            from django.conf import settings
            setattr(settings, 'STATIC_ROOT', STATIC_ROOT)
            setattr(settings, 'MEDIA_ROOT', MEDIA_ROOT)
            from django.test.utils import get_runner
            TestRunner = get_runner(settings)

            test_runner = TestRunner(interactive=False)
            failures = test_runner.run_tests(('maja_newsletter',))
    sys.exit(failures)


if __name__ == '__main__':
    main()
