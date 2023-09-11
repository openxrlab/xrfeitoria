"""
From:
https://github.com/Delgan/loguru/blob/master/docs/_extensions/autodoc_stub_file.py

Small Sphinx extension intended to generate documentation for stub files.
"""
import sys
import types
from pathlib import Path


def get_module_docstring(filepath: Path):
    with open(filepath) as file:
        source = file.read()

    co = compile(source, filepath, 'exec')

    if co.co_consts and isinstance(co.co_consts[0], str):
        docstring = co.co_consts[0]
    else:
        docstring = None

    return docstring


def setup(app):
    module_name = 'autodoc_stub_file.xrfeitoria'
    file = Path(__file__).resolve()
    stub_path = file.parents[3] / 'xrfeitoria' / '__init__.pyi'
    docstring = get_module_docstring(stub_path)
    module = types.ModuleType(module_name, docstring)
    sys.modules[module_name] = module
