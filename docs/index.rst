.. include:: sections/links.rst

.. toctree::
   :hidden:

   sections/user_guide/index
   sections/contributor_guide/index


Unified Workflow
================

``uwtools`` is an open-source modern Python package that helps automate common tasks needed for many standard numerical weather prediction (NWP) workflows and wraps Unified Forecast System (UFS) components in a highly configurable run-time interface (a driver) that maximizes flexibility, interoperability, and usability for any UFS Application.

If you're interested in contributing, check out the :doc:`Contributor Guide <sections/contributor_guide/index>`.

For users who want to start using the toolbox and framework, take a peek at our :doc:`User Guide <sections/user_guide/index>`.

.. contents:: On this page
   :depth: 2
   :local:



The Tools
---------

All our tools are available by command line interface (CLI), with select operations supported in the Python API. The API will also give you access to the underlying object creation to do with those what you please. We hope these options will let you integrate the package into your pre-existing bash and Python scripts, and give you some handy tools to use in your day-to-day work with running NWP systems.

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

| **CLI**: ``uw config -h``
| **API**: ``import uwtools.api.config``

The uw config tool suite helps you compare, transform, modify, and even validate your configuration files. The package supports YAML, shell, Fortran namelist, and INI file formats. Each of these formats allows you to specify values as Jinja2 templates to enable referencing other values for direct substitution or derived information (math, path building, string manipulation, etc.).

Compare Mode
............

When the Linux diff tool just doesn't work for comparing unordered namelists with mixed-case keys, this is your go-to! It also works on the other file types, but the Fortran namelists are the *real* catalyst behind this gem!

| See CLI examples here: :any:`Examples<compare_configs_cli_examples>`
| This mode is not supported in the API.


Realize Mode
............

This mode does the work of rendering values created by Jinja2 templates, and lets you override settings in one file with those from others, not necessarily with the same file type. With ``uwtools``, you can even reference the content of other files to build up a configuration file from its pieces.

| See CLI examples here: :any:`Examples<realize_configs_cli_examples>`

Translate Mode
..............
This is a more limited tool that helps transform legacy configuration files templated with the atparse tool (common at NOAA) into a Jinja2 template for use with the uw config realize and uw template render tools.

| See CLI examples here: :any:`Examples<translate_configs_cli_examples>`
| This mode is not supported in the API.

Validate Mode
.............
In this mode, you can provide a JSON Schema file alongside your configuration file to check to ensure that it meets the requirements set by the schema. We’ve enabled robust logging to make it easier to repair your config files when problems arise.

| See CLI examples here: :any:`Examples<validate_configs_cli_examples>`


Templating
~~~~~~~~~~

| **CLI**: ``uw template -h``
| **API**: ``import uwtools.api.template``


This one is pretty straightforward. It has a single ``render`` mode that gives you the full power of rendering a Jinja2 template in the same easy-to-use interface as your other workflow tools.

| See CLI examples here: :any:`Examples<template_cli_examples>`


Rocoto Configurability
~~~~~~~~~~~~~~~~~~~~~~

| **CLI**: ``uw rocoto -h``
| **API**: ``import uwtools.api.rocoto``


This tool is all about creating a configurable interface to the `Rocoto`_ workflow manager tool that produces the Rocoto XML for a totally arbitrary set of tasks. The ``uwtools`` package defines a structured YAML interface that relies on tasks you define to run. Paired with the uw config tool suite, this interface becomes highly configurable and requires no XML syntax!


Realize Mode
............
This is where you put in your structured YAML that defines your workflow of choice and it pops out a verified Rocoto XML.

| See CLI examples here: :any:`Examples<realize_rocoto_cli_examples>`

Validate Mode
.............
Do you already have a Rocoto XML, but don't want to run Rocoto to make sure it works? Use the validate mode to check to see if Rocoto will be happy.

| See CLI examples here: :any:`Examples<validate_rocoto_cli_examples>`



The Drivers
-----------

The uwtools driver(s) live right there beside the rest of the tools in the CLI and API. These tools will be under development for the foreseeable future, but we do have a forecast driver currently available in beta testing mode.

Forecast
~~~~~~~~

| **CLI**: ``uw forecast -h``
| **API**: ``import uwtools.api.drivers.forecast``

This driver is the first of its kind (with many others to come) and takes a few pieces of information from the user – the model, the time, and a structured YAML – and it runs a forecast via batch job or as an executable. That simple.

We've helped by providing a JSON Schema that allows you to validate your YAML to ensure you’ve got it right!

Over time, we'll add many other drivers to support a variety of UFS components from pre-processing to post-processing, along with many data assimilation components.

------------------

**Disclaimer**

The United States Department of Commerce (DOC) GitHub project code is provided on an "as is" basis and the user assumes responsibility for its use. DOC has relinquished control of the information and no longer has responsibility to protect the integrity, confidentiality, or availability of the information. Any claims against the Department of Commerce stemming from the use of its GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.
