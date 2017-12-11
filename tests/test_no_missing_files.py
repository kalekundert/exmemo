#!/usr/bin/env python3

def test_favicon():
    from exmemo.sphinx import favicon_path
    print(favicon_path)
    assert favicon_path.exists()

def test_cookiecutter():
    from exmemo.cookiecutter import cookiecutter_path
    print(cookiecutter_path)
    assert cookiecutter_path.exists()

