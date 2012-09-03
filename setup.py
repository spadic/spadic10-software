#!/usr/bin/env python

from distutils.core import setup

setup(name='spadic',
      version='0.9',
      description='Susibo -> Spadic 1.0 control software',
      author='Michael Krieger',
      author_email='michael.krieger@ziti.uni-heidelberg.de',
      url='http://spadic.uni-hd.de',
      packages=['spadic'],
      scripts=['bin/spadic_app'],
      )

