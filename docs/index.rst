.. toctree::
   :hidden:

   sections/user_guide/index
   sections/contributor_guide/index

Unified Workflow Tools
======================

``uwtools`` is a modern, open-source Python package that helps automate common tasks needed for many standard numerical weather prediction (NWP) workflows. It also provides drivers to automate the configuration and execution of :ufs:`Unified Forecast System (UFS)<>` components, providing flexibility, interoperability, and usability to various UFS Applications.

If you're interested in contributing, check out the :doc:`Contributor Guide <sections/contributor_guide/index>`.

For users who want to start using the toolbox and framework, take a peek at our :doc:`User Guide <sections/user_guide/index>`.

.. contents:: On This Page:
   :depth: 2
   :local:

The Tools
---------

The tools are accessible from both a command-line interface (CLI) and a Python API. The CLI automates many operations commonly needed in NWP workflows. The API supports all CLI operations and additionally provides access to in-memory objects to facilitate more novel use cases. We hope these options will let you integrate the package into your pre-existing bash and Python scripts, and give you some handy tools to use in your day-to-day work with running NWP systems.

Configuration Management
^^^^^^^^^^^^^^^^^^^^^^^^

| **CLI**: ``uw config -h``
| **API**: ``import uwtools.api.config``

The config tool suite helps you compare, transform, modify, and even validate your configuration. The package supports YAML, shell, Fortran namelist, and INI file formats. Configuration in any of these formats may use :jinja2:`Jinja2 syntax<templates>` to express values. These values can reference others, or compute new values by evaluating mathematical expressions, building paths, manipulating strings, etc.

Compare Mode
""""""""""""

When the Linux diff tool just doesn't work for comparing unordered namelists with mixed-case keys, this is your go-to! The Fortran namelists are the *real* catalyst behind this gem, but it also works on the other configuration formats.

| :any:`CLI documentation with examples<cli_config_compare_examples>`

Realize Mode
""""""""""""

This mode renders values created by :jinja2:`Jinja2 templates<templates>`, and lets you override values in one file or object with those from others, not necessarily with the same configuration format. With ``uwtools``, you can even reference the contents of other files to build up a configuration from its pieces.

| :any:`CLI documentation with examples<cli_config_realize_examples>`

Validate Mode
"""""""""""""

In this mode, you can provide a :json-schema:`JSON Schema<>` file alongside your configuration to validate that it meets the requirements set by the schema. We've enabled robust logging to make it easier to repair your configs when problems arise.

| :any:`CLI documentation with examples<cli_config_validate_examples>`

Templating
^^^^^^^^^^

| **CLI**: ``uw template -h``
| **API**: ``import uwtools.api.template``

Render Mode
"""""""""""

The ``render`` mode that gives you the full power of rendering a :jinja2:`Jinja2 template<templates>` in the same easy-to-use interface as your other workflow tools.

| :any:`CLI documentation with examples<cli_template_render_examples>`

Translate Mode
""""""""""""""

This tool helps transform legacy configuration files templated with the atparse tool (common at :noaa:`NOAA<>`) into :jinja2:`Jinja2 templates<templates>` for use with the ``uw config realize`` and ``uw template render`` tools, or their API equivalents.

| :any:`CLI documentation with examples<cli_template_translate_examples>`

File/Directory Provisioning
^^^^^^^^^^^^^^^^^^^^^^^^^^^

| **CLI**: ``uw fs -h``
| **API**: ``import uwtools.api.fs``


This tool helps users define the source and destination of files to be copied or linked, or directories to be created, in the same UW YAML language used by UW drivers.

| :any:`CLI documentation with examples<cli_fs_mode>`

There is a video demonstration of the use of the ``uw fs`` tool (formerly ``uw file``) available via YouTube.

.. raw:: html

   <iframe width="560" height="315" src="https://www.youtube.com/embed/b2HXOlt-Ulw?si=rLWatBFu4mvNR65S" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

Rocoto Configurability
^^^^^^^^^^^^^^^^^^^^^^

| **CLI**: ``uw rocoto -h``
| **API**: ``import uwtools.api.rocoto``

This tool is all about creating a configurable interface to the :rocoto:`Rocoto<>` workflow manager tool that produces the Rocoto XML for a totally arbitrary set of tasks. The ``uwtools`` package defines a structured YAML interface that relies on tasks you define to run. Paired with the uw config tool suite, this interface becomes highly configurable and requires no XML syntax!

Realize Mode
""""""""""""

This is where you put in your structured YAML that defines your workflow of choice, and it pops out a verified Rocoto XML.

| :any:`CLI documentation with examples<cli_rocoto_realize_examples>`

Validate Mode
"""""""""""""

Do you already have a Rocoto XML but don't want to run Rocoto to make sure it works? Use the validate mode to check to see if Rocoto will be happy.

| :any:`CLI documentation with examples<cli_rocoto_validate_examples>`

The Drivers
-----------

Drivers for NWP components are available as top-level CLI modes and API modules.

Provided with a valid UW YAML configuration file, and CLI arguments when required, ``uw`` can prepare a fully provisioned run directory and execute a component either directly on the current system, or via a batch job submitted to an HPC scheduler.

Each driver produces a list of available ``TASK`` arguments from its CLI ``--help, -h`` flag. The ``provisioned_rundir`` will do everything except ``run`` the executable, but any of the tasks may be requested and only the steps required to produce that task will be performed.

Over time, we'll add many other drivers to support a variety of UFS components from pre-processing to post-processing, along with many data assimilation components.

Drivers for UFS
^^^^^^^^^^^^^^^

To prepare a complete forecast, drivers would typically be run in the order shown here (along with additional drivers still in development).

cdeps
"""""

| **CLI**: ``uw cdeps -h``
| **API**: ``import uwtools.api.cdeps``

esg_grid
""""""""

| **CLI**: ``uw esg_grid -h``
| **API**: ``import uwtools.api.esg_grid``

filter_topo
"""""""""""

| **CLI**: ``uw filter_topo -h``
| **API**: ``import uwtools.api.filter_topo``

global_equiv_resol
""""""""""""""""""

| **CLI**: ``uw global_equiv_resol -h``
| **API**: ``import uwtools.api.global_equiv_resol``

make_hgrid
""""""""""

| **CLI**: ``uw make_hgrid -h``
| **API**: ``import uwtools.api.make_hgrid``

make_solo_mosaic
""""""""""""""""

| **CLI**: ``uw make_solo_mosaic -h``
| **API**: ``import uwtools.api.make_solo_mosaic``

orog
""""

| **CLI**: ``uw orog -h``
| **API**: ``import uwtools.api.orog``

orog_gsl
""""""""

| **CLI**: ``uw orog_gsl -h``
| **API**: ``import uwtools.api.orog_gsl``

sfc_climo_gen
"""""""""""""

| **CLI**: ``uw sfc_climo_gen -h``
| **API**: ``import uwtools.api.sfc_climo_gen``

shave
"""""

| **CLI**: ``uw shave -h``
| **API**: ``import uwtools.api.shave``

chgres_cube
"""""""""""

| **CLI**: ``uw chgres_cube -h``
| **API**: ``import uwtools.api.chgres_cube``

FV3
"""

| **CLI**: ``uw fv3 -h``
| **API**: ``import uwtools.api.fv3``

UPP
"""

| **CLI**: ``uw upp -h``
| **API**: ``import uwtools.api.upp``

Driver for JEDI
^^^^^^^^^^^^^^^

IODA
""""

| **CLI**: ``uw ioda -h``
| **API**: ``import uwtools.api.ioda``

JEDI
""""

| **CLI**: ``uw jedi -h``
| **API**: ``import uwtools.api.jedi``

Drivers for MPAS
^^^^^^^^^^^^^^^^

Drivers for working with standalone :mpas:`Model for Prediction Across Scales (MPAS)<>`, typically run in the order shown here:

ungrib
""""""

| **CLI**: ``uw ungrib -h``
| **API**: ``import uwtools.api.ungrib``

mpas_init
"""""""""

| **CLI**: ``uw mpas_init -h``
| **API**: ``import uwtools.api.mpas_init``

mpas
""""

| **CLI**: ``uw mpas -h``
| **API**: ``import uwtools.api.mpas``

------------------

**Disclaimer**

The United States Department of Commerce (DOC) GitHub project code is provided on an "as is" basis and the user assumes responsibility for its use. DOC has relinquished control of the information and no longer has responsibility to protect the integrity, confidentiality, or availability of the information. Any claims against the Department of Commerce stemming from the use of its GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.
