.. _introduction:

*******************
Introduction
*******************

.. _overview:
--------
Overview
--------

The Unified Workflow is an expanding toolbox of standalone tools that can be applied to common technical challenges faced in the implementation of any numerical weather prediction (NWP) workflow. The tools are Python-based and give users consistent, easy to use interfaces to help create and maintain a host of NWP workflows. The Users Guide will provide the overview of the current state of the supported tools ready for use.

.. _tools:
---------
The Tools
---------

.. _at_parse_to_jinja2:
^^^^^^^^^^^^^^^^^^^^
atparse_to_jinja2.py
^^^^^^^^^^^^^^^^^^^^

This tool turns any atparse enabled template into a Jinja2 enabled template for backward compatibility with many existing UFS components and applications.

.. _templater:
^^^^^^^^^^^^
templater.py
^^^^^^^^^^^^

templater.py takes in any Jinja2 template file and renders it with user-supplied values. The user-supplied values can be YAML files, INI files, Fortran namelists, or environment variables. 

.. _set_config:
^^^^^^^^^^^^^
set_config.py
^^^^^^^^^^^^^

set_config.py transforms a "base" config file into a fully formed, app-ready file that is fully configurable by the end user. It allows input 
configurations in three formats: YAML, INI, or Fortran namelist, and integrates all formats with Jinja2 templates to enable cross-referencing keys, performing math options, or introducing Jinja2-supported control structures in the definition of values

The user can supply values to overwrite any settings in the "base" configuration via YAML, INI, Fortran namelist, or environment variables. Input and output types need not be the same--for example, a Fortran namelist can be configured via a YAML config file.
set_config.py supports the creation of a field_table for the UFS Weather Model given a YAML file.
