#!/usr/bin/env python

from distutils.core import setup

setup(name='blogpost',
      version='0.1',
      description='Simple blog publisher',
      author='Suresh Jayaraman',
      author_email='sureshjayaram@gmail.com',
      scripts=['bin/blogpost'],
      license='GPLv2',
      data_files=[('share/blogpost/pixmaps',['pixmaps/stock_insert_image.png','pixmaps/stock_link.png'])]
)
