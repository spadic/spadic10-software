#!/usr/bin/env python

import subprocess
import sys
import time
from distutils.core import setup
from distutils.command.build_py import build_py


# how to get and replace the version number

try:
    cmd = 'git describe --tags'.split()
    VER = subprocess.check_output(cmd).strip().lstrip('v')
except (OSError, subprocess.CalledProcessError):
    VER = None

VERSION_STR = """# generated by {BY} at {DATE}
__version__ = "{VERSION}"
"""

def replace_version(filename, version):
    with open(filename, 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        f.truncate()
        for line in lines:
            if line.startswith('__version__'):
                f.write(VERSION_STR.format(
                          BY=sys.argv[0],
                          DATE=time.asctime(time.localtime()),
                          VERSION=version))
            else:
                f.write(line)


# inject version replacement code into build_py step of setup

class BuildPyGitVersion(build_py):
    def build_module(self, module, module_file, package):
        result = build_py.build_module(self, module, module_file, package)

        if (package, module) == ('spadic', '__init__'):
            outfile = self.get_module_outfile(self.build_lib, [package], module)
            if VER:
                replace_version(outfile, VER)
                print "replaced version in", outfile

        return result

if not VER:
    from spadic import __version__ as VER

setup(name='spadic',
      version=VER,
      description='Susibo -> Spadic 1.0 control software',
      author='Michael Krieger',
      author_email='michael.krieger@ziti.uni-heidelberg.de',
      url='http://spadic.uni-hd.de',
      packages=['spadic', 'spadic.control', 'spadic.control.ui'],
      scripts=['spadic_control', 'spadic_server'],
      cmdclass={'build_py': BuildPyGitVersion}
      )

