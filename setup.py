import os
import subprocess as sp
import sys
from setuptools import setup, find_packages
from setuptools.command.install import install


class CustomInstallCommand(install):
    """Custom install command that checks for C compiler (gcc or clang) and gperf."""

    def _installed(self, cmd):
        return sp.run([cmd, '--version'], capture_output=True).returncode == 0

    def run(self):

        # Check for C compiler (gcc or clang)
        if not self._installed('gcc') and not self._installed('clang'):
            print("Warning: No C compiler found (gcc or clang). Some parts of the package may not compile correctly.")
        
        # Check for gperf
        if not self._installed('gperf'):
            print("Warning: gperf not found. Some parts of the package may not work as expected.")
        
        # Proceed with the regular installation
        install.run(self)


setup(
    name="gperf-dict",
    version="0.1.0",
    packages=find_packages(),
    cmdclass={
        'install': CustomInstallCommand,
    },
    install_requires=[
        # Add any dependencies you might have here
        'cffi'
    ],
)
