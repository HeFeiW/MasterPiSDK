"""Setup."""

from distutils import core
import os

from setuptools import find_packages


here = os.path.abspath(os.path.dirname(__file__))
try:
  README = open(os.path.join(here, 'README.md'), encoding='utf-8').read()
except IOError:
  README = ''


install_requires = [
    'numpy',
    'matplotlib',
    'opencv-python',
    'smbus2',
]


core.setup(
    name='MasterPi',
    version='0.1',
    description='MasterPi related SDK.',#TODO
    long_description='\n\n'.join([README]),
    long_description_content_type='text/markdown',
    author='Hiwonder, THU ASTA',#TODO
    author_email='',#TODO
    url='',#TODO
    packages=find_packages(),
    install_requires=install_requires,
)
