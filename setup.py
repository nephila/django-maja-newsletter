import os
from setuptools import setup
from setuptools import find_packages

import maja_newsletter


setup(name='django-maja-newsletter',
      version=maja_newsletter.__version__,
      description='A Django app for sending newsletter by email to a contact list.',
      long_description=open('README.rst').read() + '\n' +
                       open(os.path.join('docs', 'HISTORY.txt')).read(),
      keywords='django, newsletter, mailing',
      classifiers=[
          'Framework :: Django',
          'Programming Language :: Python',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'License :: OSI Approved :: BSD License',
          'Development Status :: 5 - Production/Stable',
          'Topic :: Software Development :: Libraries :: Python Modules',],

      author=maja_newsletter.__author__,
      author_email=maja_newsletter.__email__,
      url=maja_newsletter.__url__,

      license=maja_newsletter.__license__,
      packages=find_packages(exclude=['demo']),
      include_package_data=True,
      zip_safe=False,
      install_requires=['setuptools',
                        'html2text',
                        'python-dateutil==1.5',
                        'BeautifulSoup',
                        'django-tagging',
                        'vobject',
                        'xlwt',
                        'xlrd',
                        'django-filebrowser-no-grappelli-nph',
                        'premailer'
                        ])
