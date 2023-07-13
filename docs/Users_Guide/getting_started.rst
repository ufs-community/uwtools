.. _getting_started:

***************
Getting Started
***************

.. _dependencies:

------------------------
Package Dependencies
------------------------

.. role:: raw-html(raw)
   :format: html	  

.. list-table:: UW Tools Requirements
  :widths: auto
  :header-rows: 1
		
  * - Name
    - Version
    - Source
    - Description 

  * - boto3
    - >=1.22.13
    - https://anaconda.org/conda-forge/boto3
    - 
        allows Python developers to write software 
        that makes use of services like Amazon 
        S3 and Amazon EC2
  * - black
    -
    -
    -

  * - f90nml
    - >=1.4.3
    - https://pypi.org/project/f90nml/
    -   provides a simple interface for 
        reading, writing, and modifying Fortran 
        namelist files

  * - Jinja2
    - 3.0.0
    - https://jinja.palletsprojects.com/en/3.1.x/
    -   templating tool

  * - numpy
    - >=1.21.6
    - https://numpy.org/
    -   library used for scientific computing

  * - pylint
    - 
    - https://pypi.org/project/pylint/
    -   static code analyzer that checks for  
        errors and enforces coding standards
 
  * - pytest
    - 
    - https://docs.pytest.org/en/7.2.x/
    -   testing framework

  * - pyyaml
    - >=6.0
    - https://pypi.org/project/PyYAML/
    -   YAML parser

  * - tox
    -
    -
    -
    
.. _new_installation:

-------------------
Installation [#f1]_
-------------------

^^^^^^^^^^^^^^^^^^^^^^^^^^
Using a Python Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^

Users may follow the instructions provided in this section to install conda and/or create virtual environments for their projects. These steps are not required to install or run the Unified Workflow Tools package (``uwtools``). However, use of conda virtual environments can make it easier to work on multiple projects with conflicting dependencies on the same machine. Go to :numref:`Section %s <new_uwinstall>` to skip directly to ``uwtools`` installation. 

^^^^^
conda
^^^^^

Conda is a package manager and environment management system for Python and other programming languages. You can use conda to create isolated environments for your projects, which can help you manage dependencies and package versions. 

To create a conda environment from the workflow-tools provide
environment.yaml file, follow these steps:

#. Make sure you have conda installed on your system. If not, you can install it from the official website (https://docs.conda.io/en/latest/miniconda.html) or using your operating system's package manager.

#. Open a terminal or command prompt and navigate to the directory where you want to create the conda environment.

#. Use the ``conda env create`` command to create a new conda environment. Specifically for workflow-tools type::

      conda env create -f environment.yaml

#. This will create a new conda environment called ``workflow_tools``, using the specified version of Python.

#. To activate the conda environment, use the following command::

      conda activate workflow_tools

#. You should now see ``( workflow_tools )`` in the terminal prompt, indicating that the environment is active.

#. To deactivate the conda environment, use the following command::

      conda deactivate

#. You can now use the conda environment as a sandbox for your projects,
   installing packages and running scripts without affecting the global
   Python environment. The ``workflow_tools`` environment has all the
   packages needed, but if you'd like to install others, you can.  To
   install packages in the conda environment, activate the conda
   environment. Then use the conda install command, followed by the
   package name. For example::

      conda install numpy

   This will install the ``numpy`` package in the active conda environment.
   Running the commands below for installing ``uwtools`` will install all
   the necessary packages, so there is no need to install those manually
   in this step.

^^^^^^^^^^
virtualenv
^^^^^^^^^^

A virtual environment is a tool used to isolate specific Python environments on a single machine, allowing you to work on multiple projects with different packages and package versions. 

To create a virtual environment, follow these steps:

#. Make sure you have Python and the ``venv`` module installed on your system. If not, you can install them from the official website (https://www.python.org/) or using your operating system's package manager.

#. Open a terminal or command prompt and navigate to the directory where you want to create the virtual environment.

#. Use the ``python3 -m venv`` command to create a new virtual environment. Replace ``myenv`` with the name you want to give to your virtual environment::

      python3 -m venv myenv

#. This will create a new directory called ``myenv``, which contains the files for the virtual environment.

#. To activate the virtual environment, use the following command::

      source myenv/bin/activate

#. You should now see the name of your virtual environment in the terminal prompt, indicating that it is active.

#. To deactivate the virtual environment, use the following command::

      deactivate

#. You can now use the virtual environment as a sandbox for your Python projects, installing packages and running scripts without affecting the global Python environment.


.. _new_uwinstall:

-------------------
The uwtools package
-------------------

To install the ``workflow-tools`` repository from GitHub, follow these steps:

#. Make sure you have Git installed on your system. If not, you can install it from the official website (https://git-scm.com/) or use your operating system's package manager.

#. Open a terminal or command prompt and navigate to the directory where you want to install the repository.

#. Use the following command to clone the repository::

      git clone https://github.com/ufs-community/workflow-tools.git

#. This will create a new directory called ``workflow-tools`` in the current directory, containing the files from the repository.

#. Switch to the ``workflow-tools`` directory by using the ``cd`` command::

      cd workflow-tools

#. The repository supports users by providing conda and virtualenv recipes in its top level directory. The user should choose one of these methods for installing the necessary packages to support ``workflow-tools``.

   To install with pip and virtualenv, with your virtualenv activated::

      pip install -r requirements.txt

   To install a conda environment for use with the uwtools package,
   follow the directions in the conda section above.


#. The workflow-tools repository is not currently packaged (i.e., for a pip or conda installation). To point to your local installation, start by typing the following, substituting <workflow-tools location> with the location of your :

      export PYTHONPATH=<workflow-tools location>/src:$PYTHONPATH

   This will install all the necessary packages for the tools to run.

#. You can now use the tools by running the appropriate scripts. For example, to use the templater tool, you can run the following command::

      python scripts/templater.py -h

   As of April 6, 2023, the output from this command is::

      usage: templater.py [-h] [-o OUTFILE] -i INPUT_TEMPLATE [-c CONFIG_FILE] [-d] [--values-needed] [-v] [-q] [KEY=VALUE ...]

      Update a Jinja2 Template with user-defined settings.

      positional arguments:
      KEY=VALUE Any number of configuration settings that will override values found in YAML or user environment.

      optional arguments:
      -h, --help show this help message and exit
      -o OUTFILE, --outfile OUTFILE
      Full path to output file
      -i INPUT_TEMPLATE, --input-template INPUT_TEMPLATE
      Path to a Jinja2 template file.
      -c CONFIG_FILE, --config-file CONFIG_FILE
      Optional path to a YAML configuration file. If not provided, os.environ is used to configure.
      -d, --dry-run If provided, print rendered template to stdout only
      --values-needed If provided, print a list of required configuration settings to stdout
      -v, --verbose If provided, print all logging messages.
      -q, --quiet If provided, print no logging messages

   .. note:: 

      Additional flags/option may be added at any time. The development team will rarely remove or change flag, but this may also happen from time to time. 

.. [#f1] The contents of the Installation Guide have been compiled with
   the help of OpenAI.
