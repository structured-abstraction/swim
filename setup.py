#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='swim',
    version='1.11.18',
    setup_requires=['setuptools_scm'],
    description='SWIM is a simple web information manager',
    author='Structured Abstraction',
    author_email='admin@structuredabstraction.com',
    url='https://bitbucket.org/strabs/swim',
    include_package_data=True,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
)
