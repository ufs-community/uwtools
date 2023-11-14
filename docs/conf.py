# See https://www.sphinx-doc.org/en/master/usage/configuration.html

import json
import os

### sys.path.insert(0, os.path.abspath("."))

with open("../recipe/meta.json", "r", encoding="utf-8") as f:
    metadata = json.loads(f.read())

# Project information

project = "Unified Workflow"
release = metadata["version"]
version = metadata["version"]
# rst_epilog = f"""
# .. |copyright|    replace:: {copyright}
# .. |author_list|  replace:: {author_list}
# .. |release_date| replace:: {release_date}
# .. |release_year| replace:: {release_year}
# """

# General configuration

# extensions = ["sphinx.ext.autodoc", "sphinx.ext.intersphinx"]
# suppress_warnings = ["ref.citation"]
numfig = True
numfig_format = {"figure": "Figure %s"}

# Options for HTML output

# html_css_files = ["theme_override.css"]
# html_theme_path = ["_themes"]
html_logo = os.path.join("_static", "UFS_image.png")
html_static_path = ["_static"]
html_theme = "sphinx_rtd_theme"

# Intersphinx control
# intersphinx_mapping = {"numpy": ("https://docs.scipy.org/doc/numpy/", None)}
