# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'goblin_cbm_runner'
copyright = '2023-2026, Colm Duffy'
author = 'Colm Duffy'
release = '0.6.1'

# .md and .ipynb are registered by myst_nb (which claims ".md" under its own
# parser name); .rst is built in. Do not map ".md" to "markdown" here — that
# name belongs to myst_parser, which myst_nb does not load.

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_nb",
    "autoapi.extension",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'html', 'Thumbs.db', '.DS_Store']
# Force AutoAPI to output Markdown files
autoapi_markdown_enabled = False

autoapi_options = [
    'members',
    'undoc-members',       # <--- CRITICAL: Keeps modules from being skipped if docstrings are thin
    'show-inheritance',
    'show-module-summary',
    'special-members',
    'imported-members',
]

# The example notebooks drive full CBM simulations that require the bundled
# databases and take minutes to run. Render them as authored (do not execute at
# build time) so the docs build is fast and deterministic. To regenerate live
# outputs, run the matching scripts in ``tests/examples/`` and set this to "auto".
nb_execution_mode = "off"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

autoapi_dirs = ["../src/goblin_cbm_runner"]  # location to parse for API reference
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
