# -- Path setup --------------------------------------------------------------
import os, sys
from pathlib import Path
import importlib

HERE = Path(__file__).resolve().parent      # .../module_4/docs/source
PROJECT_ROOT = HERE.parent.parent           # .../module_4  (PARENT of src)

# Put the parent on sys.path so `import src` works
sys.path.insert(0, str(PROJECT_ROOT))

print("CONF DEBUG: PROJECT_ROOT =", PROJECT_ROOT)
print("CONF DEBUG: PROJECT_ROOT exists =", PROJECT_ROOT.exists())
try:
    m = importlib.import_module("src")
    print("CONF DEBUG: import src -> OK at", Path(m.__file__).resolve())
except Exception as e:
    print("CONF DEBUG: import src FAILED ->", e)
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Grad Cafe Analytics'
copyright = '2025, Kevin G Householder'
author = 'Kevin G Householder'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",              # lets you write .md pages
    "sphinx_autodoc_typehints", # formats type hints
]

autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
