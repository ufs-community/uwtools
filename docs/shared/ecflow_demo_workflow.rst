:orphan:

.. _demonstration_workflow:

ecFlow Demonstration Workflow
-----------------------------

This repository includes a simple demonstration ecFlow workflow implemented as a Jupyter notebook.

View-Only
^^^^^^^^^

.. raw:: html

   <a href="../../../../_static/ecflow.html">Click here to view a pre-rendered version of the workflow notebook</a>
   <br><br>

Live Interaction
^^^^^^^^^^^^^^^^

To bootstrap a virtual environment and run the notebook live:

#. Select an appropriate system to run the demo on. As written, the notebook runs two local tasks, as well as a remote task implemented as a Slurm batch job, so a system with the Slurm batch scheduler would be appropriate. The environment requires ~5.5 GB, so use a filesystem with sufficient quota.
#. Ensure that X forwarding is enabled and ``ssh`` to your selected system.
#. Ensure that ``x-www-browser`` is on your ``PATH``. If not, create it as a symlink to the browser you'd like to use, e.g. ``firefox``. You should be able to run ``x-www-browser`` and interact with the browser via X over ssh.
#. Clone this repo on the selected system.
#. In the repo, ``cd`` to the ``notebooks/ecflow`` directory and run ``./start`` to build the environment, launch Jupyter, and interact with the notebook. You can edit the notebook cells in the browser. Depending on your needs, you might need to edit the files ``common.h`` and ``config.yaml`` externally.
