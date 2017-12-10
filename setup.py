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
        'formic-py3',
    ],
    entry_points={
        'console_scripts': [
            'exmemo=exmemo.commands.exmemo:exmemo',
        ],
        'exmemo.commands': [
            'project=exmemo.commands.project:project',
            'expt=exmemo.commands.expt:expt',
            'data=exmemo.commands.data:data',
            'protocol=exmemo.commands.protocol:protocol',

            'init=exmemo.commands.project:init',
            'config=exmemo.commands.config:config',
        ],
        'exmemo.commands.project': [
            'init=exmemo.commands.project:init',
            'root=exmemo.commands.project:root',
        ],
        'exmemo.commands.expt': [
            'ls=exmemo.commands.expt:ls',
            'new=exmemo.commands.expt:new',
            'edit=exmemo.commands.expt:edit',
            'open=exmemo.commands.expt:open',
            'build=exmemo.commands.expt:build',
        ],
        'exmemo.commands.data': [
            'ls=exmemo.commands.data:ls',
            'sync=exmemo.commands.data:sync',
            'link=exmemo.commands.data:link',
            'gel=exmemo.commands.data:gel',
        ],
        'exmemo.commands.protocol': [
            'ls=exmemo.commands.protocol:ls',
            'show=exmemo.commands.protocol:show',
            'print=exmemo.commands.protocol:printer',
            'save=exmemo.commands.protocol:save',
            'plugins=exmemo.commands.protocol:plugins',
        ],
        'exmemo.protocolreaders': [
            'txt=exmemo.readers:TxtReader',
            'exe=exmemo.readers:ScriptReader',
            'doc=exmemo.readers:DocReader',
            'pdf=exmemo.readers:PdfReader',
        ],
        'exmemo.datacollectors': [
            'rsync=exmemo.collectors:RsyncCollector',
            'usb=exmemo.collectors:UsbCollector',
        ],
    },
    classifiers=[
            'Topic :: Scientific/Engineering',
            'Intended Audience :: Science/Research',
            'Programming Language :: Python :: 3 :: Only',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Development Status :: 2 - Pre-Alpha',
    ],
)
