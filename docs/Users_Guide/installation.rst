.. _installation:

*******************
Installation [#f1]_
*******************

--------------------------
Using a Python Environment
--------------------------

^^^^^^^^^^
virtualenv
^^^^^^^^^^
A virtual environment is a tool used to isolate specific Python environments on a single machine, allowing you to work on multiple projects with different packages and package versions.

To create a virtual environment, follow these steps:

#. Make sure you have Python and the venv module installed on your system. If not, you can install them from the official website (https://www.python.org/) or using your operating system's package manager.

#. Open a terminal or command prompt and navigate to the directory where you want to create the virtual environment.

#. Use the python3 -m venv command to create a new virtual environment. Replace `myenv` with the name you want to give to your virtual environment::

      python3 -m venv myenv

#. This will create a new directory called `myenv`, which contains the files for the virtual environment.

#. To activate the virtual environment, use the following command::

      source myenv/bin/activate

#. You should now see the name of your virtual environment in the terminal prompt, indicating that it is active.

#. To deactivate the virtual environment, use the following command::

      deactivate

#. You can now use the virtual environment as a sandbox for your Python projects, installing packages and running scripts without affecting the global Python environment.


^^^^^
conda
^^^^^

Conda is a package manager and environment management system for Python and other programming languages. You can use conda to create isolated environments for your projects, which can help you manage dependencies and package versions.

To create a conda environment, follow these steps:

#. Make sure you have conda installed on your system. If not, you can install it from the official website (https://docs.conda.io/en/latest/miniconda.html) or using your operating system's package manager.

#. Open a terminal or command prompt and navigate to the directory where you want to create the conda environment.

#. Use the `conda create` command to create a new conda environment. Replace `myenv` with the name you want to give to your environment, and `python=3.8` with the desired version of Python::

      conda create --name myenv python=3.8

#. This will create a new conda environment called `myenv`, using the specified version of Python.

#. To activate the conda environment, use the following command::

      conda activate myenv

#. You should now see the name of your conda environment in the terminal prompt, indicating that it is active.

#. To deactivate the conda environment, use the following command::

      conda deactivate

#. You can now use the conda environment as a sandbox for your projects, installing packages and running scripts without affecting the global Python environment. To install packages in the conda environment, use the conda install command, followed by the package name. For example::

      conda install numpy

#. This will install the numpy package in the active conda environment.
   Running the commands below for installing uwtools will install all
   the necessary packages, so there is no need to install those manually
   in this step.


-------------------
The uwtools package
-------------------

To install the workflow-tools repository from Github, follow these steps:

#. Make sure you have Git installed on your system. If not, you can install it from the official website (https://git-scm.com/) or using your operating system's package manager.

#. Open a terminal or command prompt and navigate to the directory where you want to install the repository.

#. Use the following command to clone the repository::

      git clone https://github.com/ufs-community/workflow-tools.git

#. This will create a new directory called `workflow-tools` in the current directory, containing the files from the repository.

#. Change into the `workflow-tools` directory by using the `cd` command::

      cd workflow-tools

#. The repository is packaged as a pip Python package and managed via `setup.py`. Installing the package by typing ::

      pip install .

#. This will install all the necessary packages for the tools to run.

#. You can now use the tools by running the appropriate scripts. For example, to use the templater tool, you can run the following command::

      python src/uwtools/templater.py -h



.. [#f1] The contents of the Installation Guide have been compiled with
   the help of OpenAI.
