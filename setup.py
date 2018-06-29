#!/usr/bin/env python

from setuptools import setup
from spadic import __version__

setup(name='spadic',
      version=__version__,
      description='Susibo -> Spadic 1.0 control software',
      author='Michael Krieger',
      packages=['spadic',
                'spadic.control',
                'spadic.control.ui']
     )
