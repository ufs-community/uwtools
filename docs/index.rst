################
Unified Workflow
################

The idea of a unified workflow is to develop a wide array of tools in object-oriented Python that can be used in all `Unified Forecast System (UFS) <https://ufscommunity.org/>`__ applications. The Python programming language is widely used and now available on all  High-Performance Computing (HPC) platforms. It has many features that make it the language of choice for building modular, independent tool sets. These tools can be used to perform minuscule tasks such as movement of files within or across systems, manipulating datetime objects, parsing and populating configuration files, and executing and processing a series of functions in a job or a task within an application suite. The application suites can range from a single deterministic forecast to an ensemble of forecasts to cycled data assimilation systems. The application suites are not just limited to a model and data assimilation system. There are numerous examples of “workflows” in other applications, such as observation processing and ingest, post-processing of model and data assimilation generated data, reanalysis, verification and validation, deployment of products and graphics to web servers.

A schematic of the above is shown in :numref:`Schematic_Layout_Unified_Workflow_Framework` below.

.. _Schematic_Layout_Unified_Workflow_Framework:
	
.. figure:: /static/figure/Schematic_Layout_Unified_Workflow_Framework.png

   *Schematic layout of the various components of the Unified Workflow Framework.*

The tools on the right are developed as stand-alone packages that can be deployed independently on different platforms (like libraries). On the left are configuration/schema files that provide the default configurations for the workflows. These can change as the modeling systems develop. In the middle are the workflow layers that serve different needs.

Using the tools on the right, any application can assemble a unique suite for its needs. This allows all applications to retain similar implementations while at the same time providing a mechanism to construct their own flavor of the implementation. 

.. toctree::
   :hidden:
   :caption: Unified Workflow

   Users_Guide/index
   Contributors_Guide/index
