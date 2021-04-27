#!/usr/bin/env python3
# encoding: utf-8

from setuptools import setup

with open('README.rst') as file:
    readme = file.read()

setup(
    name='exmemo',
    version='0.3.0',
    author='Kale Kundert',
    author_email='kale@thekunderts.net',
    url='https://github.com/kalekundert/exmemo',
    long_description=readme,
    include_package_data=True,
    packages=[
        'exmemo',
        'exmemo.commands',
        'exmemo.cookiecutter',
        'exmemo.sphinx',
    ],
    install_requires=[
        'appdirs',
        'cookiecutter',
        'docopt',
        'formic2',
        'fossilize',
        #'metapub',
        'habanero',
        'more_itertools',
        'nonstdlib',
        'PyYAML',
        'sphinx',
        'sphinxcontrib-programoutput',
        'sphinx_rtd_theme',
        'toml',
        'wet_copy',
        'openpyxl',
        'stepwise',
    ],
    entry_points={
        'console_scripts': [
            'exmemo=exmemo.commands.main:main',
        ],
        'exmemo.commands': [
            'init=exmemo.commands.project:init',
            'new=exmemo.commands.note:new',
            'edit=exmemo.commands.note:edit',
            'open=exmemo.commands.note:open',
            'build=exmemo.commands.note:build',
            'browse=exmemo.commands.note:browse',
            'sync=exmemo.commands.data:sync',
            'link=exmemo.commands.data:link',
            'project=exmemo.commands.main:project',
            'note=exmemo.commands.main:note',
            'data=exmemo.commands.main:data',
            'config=exmemo.commands.main:config',
            'debug=exmemo.commands.main:debug',
        ],
        'exmemo.commands.project': [
            'init=exmemo.commands.project:init',
            'root=exmemo.commands.project:root',
        ],
        'exmemo.commands.note': [
            'new=exmemo.commands.note:new',
            'edit=exmemo.commands.note:edit',
            'open=exmemo.commands.note:open',
            'directory=exmemo.commands.note:directory',
            'build=exmemo.commands.note:build',
            'browse=exmemo.commands.note:browse',
            'ls=exmemo.commands.note:ls',
        ],
        'exmemo.commands.data': [
            'sync=exmemo.commands.data:sync',
            'link=exmemo.commands.data:link',
            'gel=exmemo.commands.data:gel',
            'ls=exmemo.commands.data:ls',
        ],
        'exmemo.commands.config': [
            'get=exmemo.commands.config:get',
            'set=exmemo.commands.config:set',
            'edit=exmemo.commands.config:edit',
        ],
        'exmemo.commands.debug': [
            'config=exmemo.commands.debug:config',
            'readers=exmemo.commands.debug:readers',
            'collectors=exmemo.commands.debug:collectors',
        ],
        'exmemo.datacollectors': [
            'rsync=exmemo.collectors:RsyncCollector',
            'usb=exmemo.collectors:UsbCollector',
            'gdrive=exmemo.collectors:GoogleDriveCollector',
        ],
    },
    classifiers=[
            'Topic :: Scientific/Engineering',
            'Intended Audience :: Science/Research',
            'Programming Language :: Python :: 3.6',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Development Status :: 2 - Pre-Alpha',
    ],
)
