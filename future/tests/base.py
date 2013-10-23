import os
import tempfile
from unittest import TestCase
from textwrap import dedent
from subprocess import check_output, STDOUT


class CodeHandler(TestCase):
    """
    Handy mixin for test classes for writing / reading / futurizing /
    running .py files in the test suite.
    """
    def setUp(self):
        """
        The outputs from the various futurize stages should have the following
        headers:
        """
        # After stage1:
        # TODO: use this form after implementing a fixer to consolidate
        #       __future__ imports into a single line:
        # self.headers1 = """
        # from __future__ import absolute_import, division, print_function
        # """
        self.headers1 = """
        from __future__ import absolute_import
        from __future__ import division
        from __future__ import print_function
        """[1:]

        # After stage2:
        # TODO: use this form after implementing a fixer to consolidate
        #       __future__ imports into a single line:
        # self.headers2 = """
        # from __future__ import (absolute_import, division,
        #                         print_function, unicode_literals)
        # from future import standard_library
        # from future.builtins import *
        # """
        self.headers2 = """
        from __future__ import absolute_import
        from __future__ import division
        from __future__ import print_function
        from __future__ import unicode_literals
        from future import standard_library
        from future.builtins import *
        """[1:]
        self.interpreters = ['python']
        self.tempdir = tempfile.mkdtemp() + os.path.sep
        self.env = {'PYTHONPATH': os.getcwd()}

    # def simple_convert_and_run(self, code):
    #     """
    #     Tests a complete conversion of a piece of code and whether
    #     ``futurize`` can be applied and then the resulting code be
    #     automatically run under Python 2 with the future module.

    #     The stdout and stderr from calling the script is returned.
    #     """
    #     # Translate the clean source file, then add our imports
    #     self._write_test_script(code)
    #     self._futurize_test_script()
    #     for interpreter in self.interpreters:
    #         _ = self._run_test_script(interpreter=interpreter)

    def simple_convert(self, code, stages=(1, 2), from3=False):
        """
        Returns the equivalent of ``code`` after passing it to the ``futurize``
        script.
        """
        self._write_test_script(code)
        self._futurize_test_script(stages=stages, from3=from3)
        return self._read_test_script()

    def reformat(self, code):
        """
        Removes any leading \n and dedents.
        """
        if code.startswith('\n'):
            code = code[1:]
        return dedent(code)

    def check(self, before, after=None, stages=(1, 2), from3=False, run=True):
        """
        Pass in ``before`` and (optinally) ``after``, as code blocks. If after
        is passed, we assert that the output of the conversion of ``before``
        with ``futurize`` is equal to ``after`` plus the appropriate headers
        (self.headers1 or self.headers2) depending on the stage(s) used.

        Passing stages=[1] or stages=[2] passes the flag ``--stage1`` or
        ``stage2`` to ``futurize``. Passing both stages runs ``futurize`` with
        both stages by default.

        If run is True, runs the resulting code under all Python interpreters
        in self.interpreters.

        If from3 is False, runs ``futurize`` in the default mode, converting
        from Python 2 to both 2 and 3. If from3 is True, runs ``futurize
        --from3`` to convert from Python 3 to both 2 and 3.
        """
        output = self.simple_convert(self.reformat(before), stages=stages, from3=from3)
        if run:
            for interpreter in self.interpreters:
                _ = self._run_test_script(interpreter=interpreter)
        if after is not None:
            if 2 in stages:
                headers = self.headers2
            else:
                headers = self.headers1
            desired = self.reformat(headers) + self.reformat(after)
            self.assertEqual(desired.strip(), self.order_future_lines(output).strip())

    def order_future_lines(self, code):
        """
        Returns the code block with any __future__ import lines sorted.
        """
        codelines = code.splitlines()
        future_line_numbers = [i for i in range(len(codelines)) if codelines[i].startswith('from __future__ import ')]
        sorted_future_lines = sorted([codelines[i] for i in future_line_numbers])
        # Replace the old unsorted "from __future__ import ..." lines with the
        # new sorted ones:
        codelines2 = []
        for i in range(len(codelines)):
            if i in future_line_numbers:
                codelines2.append(sorted_future_lines[i])
            else:
                codelines2.append(codelines[i])
        return '\n'.join(codelines2)

    def unchanged(self, code, stages=(1, 2), from3=False, run=True):
        """
        Tests to ensure the code is unchanged by the futurize process,
        exception for the addition of __future__ and future imports.
        """
        self.check(code, code, stages, from3, run)

    def _write_test_script(self, code, filename='mytestscript.py'):
        """
        Dedents the given code (a multiline string) and writes it out to
        a file in a temporary folder like /tmp/tmpUDCn7x/mytestscript.py.
        """
        with open(self.tempdir + filename, 'w') as f:
            f.write(dedent(code))

    def _read_test_script(self, filename='mytestscript.py'):
        with open(self.tempdir + filename) as f:
            newsource = f.read()
        return newsource

    def _futurize_test_script(self, filename='mytestscript.py', stages=(1, 2), from3=False):
        params = []
        stages = list(stages)
        if from3:
            params += ['--from3']
        if stages == [1]:
            params += ['--stage1']
        elif stages == [2]:
            params += ['--stage2']
        else:
            assert stages == [1, 2]
            # No extra params needed

        output = check_output(['python', 'futurize.py'] + params +
                              ['-w', self.tempdir + filename],
                              stderr=STDOUT)
        return output

    def _run_test_script(self, filename='mytestscript.py',
                         interpreter='python'):
        env = {'PYTHONPATH': os.getcwd()}
        return check_output([interpreter, self.tempdir + filename],
                            env=env)


