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
            'exmemo=exmemo.commands.main:main',
        ],
        'exmemo.commands': [
            'init=exmemo.commands.project:init',
            'new=exmemo.commands.expt:new',
            'edit=exmemo.commands.expt:edit',
            'open=exmemo.commands.expt:open',
            'build=exmemo.commands.expt:build',
            'show=exmemo.commands.protocol:show',
            'print=exmemo.commands.protocol:printer',
            'save=exmemo.commands.protocol:save',
            'sync=exmemo.commands.data:sync',
            'link=exmemo.commands.data:link',
            'project=exmemo.commands.main:project',
            'expt=exmemo.commands.main:expt',
            'protocol=exmemo.commands.main:protocol',
            'data=exmemo.commands.main:data',
            'config=exmemo.commands.config:config',
        ],
        'exmemo.commands.project': [
            'init=exmemo.commands.project:init',
            'root=exmemo.commands.project:root',
        ],
        'exmemo.commands.expt': [
            'new=exmemo.commands.expt:new',
            'edit=exmemo.commands.expt:edit',
            'open=exmemo.commands.expt:open',
            'build=exmemo.commands.expt:build',
            'ls=exmemo.commands.expt:ls',
        ],
        'exmemo.commands.data': [
            'sync=exmemo.commands.data:sync',
            'link=exmemo.commands.data:link',
            'gel=exmemo.commands.data:gel',
            'ls=exmemo.commands.data:ls',
        ],
        'exmemo.commands.protocol': [
            'show=exmemo.commands.protocol:show',
            'edit=exmemo.commands.protocol:edit',
            'print=exmemo.commands.protocol:printer',
            'save=exmemo.commands.protocol:save',
            'plugins=exmemo.commands.protocol:plugins',
            'ls=exmemo.commands.protocol:ls',
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
