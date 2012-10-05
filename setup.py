#!/usr/bin/env python

from distutils.core import setup

setup(name='spadic',
      version='0.92',
      description='Susibo -> Spadic 1.0 control software',
      author='Michael Krieger',
      author_email='michael.krieger@ziti.uni-heidelberg.de',
      url='http://spadic.uni-hd.de',
      packages=['spadic'],
      scripts=['scripts/spadic_app'],
      )

