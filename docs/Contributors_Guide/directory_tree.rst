**************
Directory Tree
**************

Goals
=====
* No conflicts between different packages in their external packages
* No circular dependencies
* If a user/developer introduces a new dependency, they need to add an entry in `environment.yaml` and `setup.cfg`. 
* GitHub actions should test `setup.cfg` and `environment.yaml` to ensure that our code runs correctly. 
* Packages should adhere to the following generic structure as appropriate:

Sample package structure::

   pkg
   ├── __init__.py
   ├── module1.py
   └── subpkg
     ├── __init__.py
     └── module2.py
      
* Tests follow a similar structure to code.

* Workflow tools are standalone pieces of code that can be used with other tools.
  
* Helpers can be utilized by any tool/code at any level.
  
* New tools should be added as subpackages of `uwtools`.

* New helpers should be added as modules of helpers.

Sample Structure::

  tests
   ├── test_utils
   │    ├── __init__.py
   │    ├── test_logger.py
   │    └── test_errors.py
   ├── test_scheduler
   │    ├── __init__.py
   │    └── test_slurm.py
   ├── test_runners
   │    ├── __init__.py
   │    └── test_forecast.py
  uwtools
   ├── __init__.py
   ├── scheduler
   │    ├── __init__.py
   │    ├── scheduler.py
   │    └── slurm.py
   ├── config_parser
   │    ├── __init__.py
   │    └── config_parser.py 
  runners
   ├── __init__.py
   │    └── forecast.py
  helpers
   └── __init__.py
        ├──logger.py
        └──exceptions.py
   
Examples of how to import this structure
In **scheduler.py**::

  import ..helpers.logger as logger

From an external source::

  import uwtools.helpers.logger as logger
