.. toctree::
   :hidden:

   sections/user_guide/index
   sections/contributor_guide/index

Unified Workflow Tools
======================

``uwtools`` is an open-source modern Python package that helps automate common tasks needed for many standard numerical weather prediction (NWP) workflows and provides drivers to automate the configuration and execution of :ufs:`Unified Forecast System (UFS)<>` components, providing flexibility, interoperability, and usability to various UFS Applications.

If you're interested in contributing, check out the :doc:`Contributor Guide <sections/contributor_guide/index>`.

For users who want to start using the toolbox and framework, take a peek at our :doc:`User Guide <sections/user_guide/index>`.

.. contents:: On this page
   :depth: 2
   :local:

The Tools
---------

The tools are accessible from both a command-line interface (CLI) and a Python API. The CLI automates many operations commonly needed in NWP workflows. The API supports all CLI operations, and additionally provides access to in-memory objects to facilitate more novel use cases. We hope these options will let you integrate the package into your pre-existing bash and Python scripts, and give you some handy tools to use in your day-to-day work with running NWP systems.

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

| **CLI**: ``uw config -h``
| **API**: ``import uwtools.api.config``

The config tool suite helps you compare, transform, modify, and even validate your configuration. The package supports YAML, shell, Fortran namelist, and INI file formats. Configuration in any of these formats may express values using :jinja2:`Jinja2 syntax<templates>`. These values can reference others, or compute new values by evaluating mathematical expressions, building paths, manipulating strings, etc.

Compare Mode
............

When the Linux diff tool just doesn't work for comparing unordered namelists with mixed-case keys, this is your go-to! It also works on the other configuration formats, but the Fortran namelists are the *real* catalyst behind this gem!

| :any:`CLI documentation with examples<compare_configs_cli_examples>`

Realize Mode
............

This mode renders values created by :jinja2:`Jinja2 templates<templates>`, and lets you override values in one file or object with those from others, not necessarily with the same configuration format. With ``uwtools``, you can even reference the content of other files to build up a configuration from its pieces.

| :any:`CLI documentation with examples<realize_configs_cli_examples>`

Translate Mode
..............

This tool helps transform legacy configuration files templated with the atparse tool (common at NOAA) into :jinja2:`Jinja2 templates<templates>` for use with the ``uw config realize`` and ``uw template render`` tools, or their API equivalents.

| :any:`CLI documentation with examples<translate_configs_cli_examples>`

Validate Mode
.............

In this mode, you can provide a :json-schema:`JSON Schema<>` file alongside your configuration to validate that it meets the requirements set by the schema. We've enabled robust logging to make it easier to repair your configs when problems arise.

| :any:`CLI documentation with examples<validate_configs_cli_examples>`

Templating
~~~~~~~~~~

| **CLI**: ``uw template -h``
| **API**: ``import uwtools.api.template``

This one is pretty straightforward. It has a single ``render`` mode that gives you the full power of rendering a :jinja2:`Jinja2 template<templates>` in the same easy-to-use interface as your other workflow tools.

| :any:`CLI documentation with examples<template_cli_examples>`

Rocoto Configurability
~~~~~~~~~~~~~~~~~~~~~~

| **CLI**: ``uw rocoto -h``
| **API**: ``import uwtools.api.rocoto``

This tool is all about creating a configurable interface to the :rocoto:`Rocoto<>` workflow manager tool that produces the Rocoto XML for a totally arbitrary set of tasks. The ``uwtools`` package defines a structured YAML interface that relies on tasks you define to run. Paired with the uw config tool suite, this interface becomes highly configurable and requires no XML syntax!

Realize Mode
............

This is where you put in your structured YAML that defines your workflow of choice and it pops out a verified Rocoto XML.

| :any:`CLI documentation with examples<realize_rocoto_cli_examples>`

Validate Mode
.............

Do you already have a Rocoto XML, but don't want to run Rocoto to make sure it works? Use the validate mode to check to see if Rocoto will be happy.

| :any:`CLI documentation with examples<validate_rocoto_cli_examples>`

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
