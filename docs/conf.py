import os
import sys
# CURRENT: sys.path.insert(0, os.path.abspath('..')) 

# NEW (Replace the line above with these 2 lines):
sys.path.insert(0, os.path.abspath('..'))
sys.path.append(os.path.abspath('C:/Users/oskar/OneDrive/Desktop/my_project'))
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Audio_spectrum_analyzer'
copyright = '2025, Oskar'
author = 'Oskar'
release = '01.12.2025'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # Helps read different docstring styles
    'sphinx.ext.viewcode',  # Adds links to source code
]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

autodoc_mock_imports = ["machine", "network", "usocket", "sh1106", "fft"]
