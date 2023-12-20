################
Unified Workflow
################

.. _Vision:

Vision
======================
The idea of a unified workflow is to develop a wide array of tools in object-oriented Python that can be used in all `Unified Forecast System (UFS) <https://ufscommunity.org/>`__ applications. The Python programming language is widely used and now available on all  High-Performance Computing (HPC) platforms. It has many features that make it the language of choice for building modular, independent tool sets. These tools can be used to perform minuscule tasks such as movement of files within or across systems, manipulating datetime objects, parsing and populating configuration files, and executing and processing a series of functions in a job or a task within an application suite. The application suites can range from a single deterministic forecast to an ensemble of forecasts to cycled data assimilation systems. The application suites are not just limited to a model and data assimilation system. There are numerous examples of “workflows” in other applications, such as observation processing and ingest, post-processing of model and data assimilation generated data, reanalysis, verification and validation, deployment of products and graphics to web servers.

A schematic of this is shown in :numref:`Schematic_Layout_Unified_Workflow_Framework`

.. _Schematic_Layout_Unified_Workflow_Framework:
	
.. figure:: /static/figure/Schematic_Layout_Unified_Workflow_Framework.png

   *Schematic layout of the various components of the Unified Workflow Framework.*

The tools on the right are developed as stand-alone packages that can be deployed independently on different platforms (like libraries). On the left are configuration/schema files that provide the default configurations for the workflows. These can change as the modeling systems develop. In the middle are the workflow layers that serve different needs.

Using the tools on the right, any application can assemble a unique suite for its needs. This allows all applications to retain similar implementations while at the same time providing a mechanism to construct their own flavor of the implementation. 

.. _UWStructure:

Directory Structure
======================
The ``workflow-tools`` :term:`repository` is an NCO-compliant repository. Its structure follows the standards laid out in :term:`NCEP` Central Operations (NCO) WCOSS `Implementation Standards <https://www.nco.ncep.noaa.gov/idsb/implementation_standards/ImplementationStandards.v11.0.0.pdf?>`__. 

.. code-block:: console

   workflow-tools
   ├── docs 
   │     └── sections
   │           ├── contributor_guide
   │           └── user_guide
   └── src
         └── (uwtools)
    	         ├── api
    	         ├── apps 
    	         ├── config
               │     └── formats
    	         ├── drivers 
    	         ├── files
               │     ├── gateway
               │     ├── interface
               │     └── model
    	         ├── resources
    	         ├── utils               
    	         └── tests
                     ├── api
                     ├── config
                     │     └── formats
                     ├── drivers
                     ├── files
                     │     ├── gateway
                     │     ├── interface
                     │     └── model
                     ├── fixtures
                     │     └── files
                     └── utils 



Unified Workflow Tools SubDirectories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:numref:`Table %s <Subdirectories>` describes the contents of the most important UW Tools subdirectories. Users can reference the `NCO Implementation Standards <https://www.nco.ncep.noaa.gov/idsb/implementation_standards/ImplementationStandards.v11.0.0.pdf?>`__ (p. 19) for additional details on repository structure in NCO-compliant repositories. 

.. _Subdirectories:

.. table:: *Subdirectories of the workflow-tools repository*

   +-------------------------+----------------------------------------------------+
   | **Directory Name**      | **Description**                                    |
   +=========================+====================================================+
   | docs                    | Repository documentation                           |
   +-------------------------+----------------------------------------------------+
   | api                     | External calls for to API                          |
   +-------------------------+----------------------------------------------------+
   | apps                    | App configurations for the forecast drivers        |
   +-------------------------+----------------------------------------------------+
   | config                  | Primary classes for handling configuration files   |
   +-------------------------+----------------------------------------------------+
   | drivers                 | Main experiment and forecast drivers               |
   +-------------------------+----------------------------------------------------+
   | resources               | Schemas used by the workflow                       |
   +-------------------------+----------------------------------------------------+
   | tests                   | Unit tests for all functions                       |
   +-------------------------+----------------------------------------------------+
   | utils                   | Utility classes used by the workflow               |
   +-------------------------+----------------------------------------------------+

.. toctree::
   :hidden:

   sections/user_guide/index
   sections/contributor_guide/index


**Disclaimer**

The United States Department of Commerce (DOC) GitHub project code is provided on an "as is" basis and the user assumes responsibility for its use. DOC has relinquished control of the information and no longer has responsibility to protect the integrity, confidentiality, or availability of the information. Any claims against the Department of Commerce stemming from the use of its GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.
