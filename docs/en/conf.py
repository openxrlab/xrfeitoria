# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

import sphinx_rtd_theme

# sys.path.insert(0, os.path.abspath('../../src/XRFeitoriaUnreal/Content/Python'))
# sys.path.insert(0, os.path.abspath('../../src/XRFeitoriaBpy'))
sys.path.insert(0, os.path.abspath('../..'))
sys.path.append(os.path.abspath('./_ext'))

# -- Project information -----------------------------------------------------

project = 'XRFeitoria'
copyright = '2023, OpenXRLab'
author = 'XRFeitoria Authors'
from xrfeitoria import __version__

# The full version, including alpha/beta/rc tags
version = __version__
release = __version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.graphviz',
    'sphinx_copybutton',
    'sphinx_gallery.load_style',
    'sphinx_tabs.tabs',
    'sphinxcontrib.autodoc_pydantic',
    'enum_tools.autoenum',
    'myst_parser',
    'nbsphinx',
    'custom_diagram',
]
autodoc_mock_imports = ['']
autosummary_generate = True
# autodoc_typehints = 'none'  # shorten typehints
autodoc_pydantic_model_show_json = True
autodoc_pydantic_model_show_config_summary = False

# notebook
nbsphinx_allow_errors = True
nbsphinx_execute = 'never'
nbsphinx_prolog = """
.. raw:: html

    <style>

        .rst-content code.literal, .rst-content tt.literal {
            color: #000000;
        }

        div.nbinput.container div.prompt,
        div.nboutput.container div.prompt {
            padding-top: 11px;
        }
        div.nbinput.container div.input_area div[class*=highlight] > pre,
        div.nboutput.container div.output_area div[class*=highlight] > pre,
        div.nboutput.container div.output_area div[class*=highlight].math,
        div.nboutput.container div.output_area.rendered_html,
        div.nboutput.container div.output_area > div.output_javascript,
        div.nboutput.container div.output_area:not(.rendered_html) > img{
            padding: 10px;
        }
    </style>
"""

# Parse `Returns` in docstr with parameter style
napoleon_custom_sections = [('Returns', 'params_style')]

# Ignore >>> when copying code
copybutton_prompt_text = r'>>> |\.\.\. '
copybutton_prompt_is_regexp = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
autodoc_default_options = {
    'member-order': 'groupwise',
    'special-members': '__init__',
}

# -- GraphViz configuration --------------------------------------------------
graphviz_output_format = 'svg'

# -- Options for HTML output -------------------------------------------------
# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_css_files = ['override.css']  # override py property
html_theme_options = {
    'navigation_depth': 3,
    # 'style_external_links': True,
    'analytics_id': 'G-F7W2BTNGLW',
}


# Enable ::: for my_st
myst_enable_extensions = ['colon_fence']

master_doc = 'index'
