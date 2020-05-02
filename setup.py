#!/usr/bin/env python
"""
sentry-googlechat
==============

A `Sentry <https://getsentry.com>`_ plugin which posts notifications
to `Google Chat <https://gsuite.google.com/products/chat/>`_.

:license: MIT, see LICENSE for more details.
"""

from setuptools import setup, find_packages
from sentry_googlechat import __version__
import os

cwd = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
readme_text = open(os.path.join(cwd, 'README.md')).read()

setup(
    name='sentry-googlechat',
    version=__version__,
    author='Jonhnny Weslley',
    author_email='jw@jonhnnyweslley.net',
    url='https://github.com/jweslley/sentry-googlechat',
    long_description=readme_text,
    long_description_content_type="text/markdown",
    license='MIT',
    description='A Sentry plugin which posts notifications to Google Chat (https://gsuite.google.com/products/chat/).',
    packages=find_packages(),
    install_requires=[
      'sentry',
    ],
    include_package_data=True,
    entry_points={
        'sentry.apps': [
            'sentry_googlechat = sentry_googlechat',
        ],
        'sentry.plugins': [
            'sentry_googlechat = sentry_googlechat.plugin:GoogleChatPlugin',
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Topic :: System :: Monitoring'
    ],
)