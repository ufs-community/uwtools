## Information

stage.Stage is the base class for staging data, staging means copying files, directories, directory trees, substituting
templates, etc..
What stage can do can be extended though the stage_factory (see __init__.py). To add functionality,
define a function or method with the following signature:
   def action(self, data, source, target, [logger]):
   where
     data is a dictionary with instructions (see specific actions)
     source is a source directory
     target is a target directory
see for example runtime.r2d2_files in ewok (implements the retrieval of data from r2d2 as a staging step)

## Anatomy of a stage file
    action:
       ...
       ...
    where action is the name of a staging step (the name the action is registered with in the factory)
          the other lines are specific to the action, see different implementations.

    There can be several different actions in the stage file.

## How to use stage

    from solo.stage import Stage

    staging = # probably read it from a yaml file, see yaml_file or create a dictionary
    stage = Stage(source, destination, staging)

    - source is the source directory reference. Usually it is where the stage yaml file is stored. All relative
      source paths in staging are in reference to source. Absolute paths are recognized as starting with '/'.
    - destination is the destination directory. All relative destination paths in staging are in reference
      to destination. Absolute paths are recognized as starting with '/'.

