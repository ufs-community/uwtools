# pylint: disable=missing-function-docstring
"""
Tests for uwtools.rocoto module.
"""

from uwtools import rocoto

# Test functions


def test_add_jobname(capsys):
    expected = {
task_hello:
  jobname: hello
  ...
metatask_howdy:
  var:
    mem: 1 2 3
  task_howdy_#mem#:
    jobname: howdy_#mem#
    ...
  task_hola_#mem#:
    jobname: hola_#mem#
    ...
  metatask_hey_#mem#:
    var:
      day: mon tues
    task_hey_#mem#_#day#:
      jobname: hey_#mem#_#day#
      ...
}

    tasks = {
task_hello:
  ...
metatask_howdy:
  var:
    mem: 1 2 3
  task_howdy_#mem#:
    ...
  task_hola_#mem#:
    ...
  metatask_hey_#mem#:
    var:
      day: mon tues
    task_hey_#mem#_#day#:
      ... 
}

    config.rocoto._add_jobname(tasks)
    actual = capsys.readoutter().out
    assert expected == actual


def test_write_rocoto_xml(tmp_path):
    pass
    # r = rocoto_module.write_rocoto_xml(input_yaml, input_template, rendered_output)
    """
    r = rocoto.RocotoXML()
    r.write(output_dir=tmp_path)
    # pylint: disable=line-too-long
    expected = "<?xml version='1.0' encoding='utf-8'?>\n<workflow>\n  <log>foo then bar</log>\n  <task>baz then qux</task>\n</workflow>"
    with open(tmp_path / "contents.xml", "r", encoding="utf-8") as f:
        assert expected == f.read()
    """

