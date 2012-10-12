from setuptools import setup
from setuptools import find_packages
#import sys, os

version = '0.0'

requires = ['statlib',
            'gevent',
            'stuf',
            'psutil',
            'supervisor']


setup(name='syswat',
      version=version,
      description="A simple utilty to blather about what is happening on a node",
      long_description=""" """,
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='whit',
      author_email='whit at surveymonkey.com',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      entry_points="""
      [console_scripts]
      cwatd=syswat.watd:carbon_main
      """)
