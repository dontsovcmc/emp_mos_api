#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Неофициальный Python клиент Единой мобильной платформы города Москвы.
"""

import sys
import platform
from setuptools import setup


VERSION_MAJOR = 0
VERSION_MINOR = 1  

ver = '%d.%d' % (VERSION_MAJOR, VERSION_MINOR)

cur = 'win32' if sys.platform == 'win32' else platform.linux_distribution()[0].lower()
ext = '.zip' if sys.platform == 'win32' else '.tar.gz'

bin_name = 'emp_mos_api-%s-%s%s' % (cur, ver, ext)


if __name__ == '__main__':

    with open('README.md', 'r') as fh:
        long_description = fh.read()

    setup(
        name='emp_mos_api',
        version=ver,
        description=__doc__.replace('\n', '').strip(),
        long_description=long_description,
        author='Dontsov E.',
        author_email='dontsovcmc@gmail.com',
        url='https://github.com/dontsovcmc/emp_mos_api',
        py_modules=['emp_mos_api'],
        include_package_data=True,
        packages=[
            'emp_mos_api'
        ],
        classifiers=(
            "Programming Language :: Python :: 2.7",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ),
        license='MIT',
        platforms=['linux2', 'win32'],
        install_requires=[
            'requests'
        ],
    )
