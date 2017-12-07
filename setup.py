#!/usr/bin/env python3
# encoding: utf-8

from setuptools import setup

with open('README.rst') as file:
    readme = file.read()

setup(
    name='exmemo',
    version='0.0.0',
    author='Kale Kundert',
    author_email='kale@thekunderts.net',
    long_description=readme,
    packages=[
        'exmemo',
    ],
    install_requires=[
        'docopt',
        'appdirs',
        'sphinx',
        'sphinx_rtd_theme',
        'sphinxcontrib-programoutput',
        'toml',
        'metapub',
    ],
    entry_points={
        'console_scripts': [
            'exmemo=exmemo.commands.exmemo:exmemo',
        ],
        'exmemo.commands': [
            'init=exmemo.commands.project:init',
            'project=exmemo.commands.project:project',
            'expt=exmemo.commands.expt:expt',
            'config=exmemo.commands.config:config',
        ],
        'exmemo.commands.project': [
            'init=exmemo.commands.project:init',
            'root=exmemo.commands.project:root',
        ],
        'exmemo.commands.expt': [
            'ls=exmemo.commands.expt:ls',
            'edit=exmemo.commands.expt:edit',
            'open=exmemo.commands.expt:open',
        ],
    },
)
