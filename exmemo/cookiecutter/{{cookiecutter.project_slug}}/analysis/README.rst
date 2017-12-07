{{ '*' * cookiecutter.project_title|length }}
{{ cookiecutter.project_title }}
{{ '*' * cookiecutter.project_title|length }}

.. image:: https://img.shields.io/pypi/v/{{ cookiecutter.project_slug }}.svg
   :target: https://pypi.python.org/pypi/{{ cookiecutter.project_slug }}

.. image:: https://img.shields.io/pypi/pyversions/{{ cookiecutter.project_slug }}.svg
   :target: https://pypi.python.org/pypi/{{ cookiecutter.project_slug }}

.. image:: https://img.shields.io/travis/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}.svg
   :target: https://travis-ci.org/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}

.. image:: https://img.shields.io/coveralls/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}.svg
   :target: https://coveralls.io/github/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}?branch=master

Installation
============
To install use pip:

    $ pip install {{ cookiecutter.project_slug }}

Or clone the repo:

    $ git clone https://github.com/{{cookiecutter.github_username}}/{{cookiecutter.project_slug}}.git
    $ python setup.py install

Usage
=====
Coming soon...
