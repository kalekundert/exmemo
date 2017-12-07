#!/usr/bin/env python3
# encoding: utf-8

from setuptools import setup

with open('README.rst') as file:
    readme = file.read()

setup(
    name='{{ cookiecutter.project_slug }}',
    version='0.0.0',
    author='{{ cookiecutter.full_name }}',
    long_description=readme,
    packages=[
        '{{ cookiecutter.project_slug }}',
    ],
    install_requires=[
    ],
    entry_points={
        'console_scripts': [
        ],
    },
    include_package_data=True,
)
