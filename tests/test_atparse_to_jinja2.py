''' Tests for the atparse_to_jinja2 tool. '''

from contextlib import redirect_stdout
import io
import os
import pathlib

from uwtools import atparse_to_jinja2

uwtools_file_base = os.path.join(os.path.dirname(__file__))

def test_all_templates_replaced(): #pylint: disable=unused-variable

    ''' Test that all atparse @[] items are replaced with Jinja2
    templates {{ }} '''

    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/ww3_multi.inp.IN"))

    args = ["-i", input_file, "-d"]

    outstring = io.StringIO()
    with redirect_stdout(outstring):
        atparse_to_jinja2.convert_template(args)

    result = outstring.getvalue()
    assert '@[' not in result
