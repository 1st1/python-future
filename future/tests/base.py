import os
import tempfile
import unittest
import sys
if not hasattr(unittest, 'skip'):
    import unittest2 as unittest
from textwrap import dedent
import subprocess

from future.utils import bind_method


# For Python 2.6 compatibility: see http://stackoverflow.com/questions/4814970/
if "check_output" not in dir(subprocess): # duck punch it in!
    def f(*popenargs, **kwargs):
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd)
        return output
    subprocess.check_output = f


def reformat(code):
    """
    Removes any leading \n and dedents.
    """
    if code.startswith('\n'):
        code = code[1:]
    return dedent(code)


class CodeHandler(unittest.TestCase):
    """
    Handy mixin for test classes for writing / reading / futurizing /
    running .py files in the test suite.
    """
    def setUp(self):
        """
        The outputs from the various futurize stages should have the
        following headers:
        """
        # After stage1:
        # TODO: use this form after implementing a fixer to consolidate
        #       __future__ imports into a single line:
        # self.headers1 = """
        # from __future__ import absolute_import, division, print_function
        # """
        self.headers1 = reformat("""
        from __future__ import absolute_import
        from __future__ import division
        from __future__ import print_function
        """)

        # After stage2 --all-imports:
        # TODO: use this form after implementing a fixer to consolidate
        #       __future__ imports into a single line:
        # self.headers2 = """
        # from __future__ import (absolute_import, division,
        #                         print_function, unicode_literals)
        # from future import standard_library
        # from future.builtins import *
        # """
        self.headers2 = reformat("""
        from __future__ import absolute_import
        from __future__ import division
        from __future__ import print_function
        from __future__ import unicode_literals
        from future import standard_library
        standard_library.install_hooks()
        from future.builtins import *
        """)
        self.interpreters = ['python']
        self.tempdir = tempfile.mkdtemp() + os.path.sep
        self.env = {'PYTHONPATH': os.getcwd()}

    def convert(self, code, stages=(1, 2), all_imports=False, from3=False,
                reformat=True, run=True):
        """
        Converts the code block using ``futurize`` and returns the
        resulting code.
        
        Passing stages=[1] or stages=[2] passes the flag ``--stage1`` or
        ``stage2`` to ``futurize``. Passing both stages runs ``futurize``
        with both stages by default.

        If from3 is False, runs ``futurize``, converting from Python 2 to
        both 2 and 3. If from3 is True, runs ``pasteurize`` to convert
        from Python 3 to both 2 and 3.

        Optionally reformats the code block first using the reformat() function.

        If run is True, runs the resulting code under all Python
        interpreters in self.interpreters.
        """
        if reformat:
            code = reformat(code)
        self._write_test_script(code)
        self._futurize_test_script(stages=stages, all_imports=all_imports,
                                   from3=from3)
        output = self._read_test_script()
        if run:
            for interpreter in self.interpreters:
                _ = self._run_test_script(interpreter=interpreter)
        return output

    def compare(self, output, expected, ignore_imports=True):
        """
        Compares whether the code blocks are equal. If not, raises an
        exception so the test fails. Ignores any trailing whitespace like
        blank lines.

        If ignore_imports is True, passes the code blocks into the
        strip_future_imports method.
        """
        # self.assertEqual(expected.rstrip(),
        #                  self.order_future_lines(output).rstrip())
        if ignore_imports:
            output = self.strip_future_imports(output)
            expected = self.strip_future_imports(expected)
        self.assertEqual(self.order_future_lines(output.rstrip()),
                         expected.rstrip())

    def strip_future_imports(self, code):
        """
        Strips any of these import lines:

            from __future__ import <anything>
            from future <anything>
            from future.<anything>

        or any line containing:
            install_hooks()

        Limitation: doesn't handle imports split across multiple lines like
        this:

            from __future__ import (absolute_import, division, print_function,
                                    unicode_literals)
        """
        output = []
        # We need .splitlines(keepends=True), which doesn't exist on Py2,
        # so we use this instead:
        for line in code.split('\n'):
            if not (line.startswith('from __future__ import ')
                    or line.startswith('from future ')
                    or 'install_hooks()' in line
                    # but don't match "from future_builtins" :)
                    or line.startswith('from future.')):
                output.append(line)
        return '\n'.join(output)

    def convert_check(self, before, expected, stages=(1, 2), all_imports=False,
                      ignore_imports=True, from3=False, run=True):
        """
        Convenience method that calls convert() and compare().

        Reformats the code blocks automatically using the reformat() function.

        If all_imports is passed, we add the appropriate import headers
        for the stage(s) selected to the ``expected`` code-block, so they
        needn't appear repeatedly in the test code.

        If ignore_imports is True, ignores the presence of any lines
        beginning:
        
            from __future__ import ...
            from future import ...
            
        for the purpose of the comparison.
        """
        output = self.convert(before, stages=stages, all_imports=all_imports,
                              from3=from3, run=run)
        if all_imports:
            headers = self.headers2 if 2 in stages else self.headers1
        else:
            headers = ''

        self.compare(output, reformat(headers + expected),
                    ignore_imports=ignore_imports)

    def order_future_lines(self, code):
        """
        TODO: simplify this hideous code ...

        Returns the code block with any ``__future__`` import lines sorted, and
        then any ``future`` import lines sorted.

        This only sorts the lines within the expected blocks:
        __future__ first, then future imports, then regular code.

        Example:
        >>> code = '''
                   # comment here
                   from __future__ import print_function
                   from __future__ import absolute_import
                                     # blank line or comment here
                   from future.builtins import zzz
                   from future.builtins import blah
                   # another comment

                   code_here
                   more_code_here
                   '''
        """
        # We need .splitlines(keepends=True), which doesn't exist on Py2,
        # so we use this instead:
        lines = code.split('\n')

        uufuture_line_numbers = [i for i, line in enumerate(lines)
                                   if line.startswith('from __future__ import ')]

        future_line_numbers = [i for i, line in enumerate(lines)
                                 if line.startswith('from future')]

        assert code.lstrip() == code, ('internal usage error: '
                'dedent the code before calling order_future_lines()')

        def mymax(numbers):
            return max(numbers) if len(numbers) > 0 else 0

        def mymin(numbers):
            return min(numbers) if len(numbers) > 0 else 0

        assert mymax(uufuture_line_numbers) <= mymin(future_line_numbers), \
                'the __future__ and future imports are out of order'

        uul = sorted([lines[i] for i in uufuture_line_numbers])
        sorted_uufuture_lines = dict(zip(uufuture_line_numbers, uul))

        fl = sorted([lines[i] for i in future_line_numbers])
        sorted_future_lines = dict(zip(future_line_numbers, fl))

        # Replace the old unsorted "from __future__ import ..." lines with the
        # new sorted ones:
        new_lines = []
        for i in range(len(lines)):
            if i in uufuture_line_numbers:
                new_lines.append(sorted_uufuture_lines[i])
            elif i in future_line_numbers:
                new_lines.append(sorted_future_lines[i])
            else:
                new_lines.append(lines[i])
        return '\n'.join(new_lines)

    def unchanged(self, code, **kwargs):
        """
        Convenience method to ensure the code is unchanged by the
        futurize process.
        """
        self.convert_check(code, code, **kwargs)

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

    def _futurize_test_script(self, filename='mytestscript.py', stages=(1, 2),
                              all_imports=False, from3=False):
        params = []
        stages = list(stages)
        if all_imports:
            params.append('--all-imports')
        if from3:
            script = 'pasteurize.py'
        else:
            script = 'futurize.py'
            if stages == [1]:
                params.append('--stage1')
            elif stages == [2]:
                params.append('--stage2')
            else:
                assert stages == [1, 2]
            # No extra params needed

        output = subprocess.check_output(['python', script] + params +
                                         ['-w', self.tempdir + filename],
                                         stderr=subprocess.STDOUT)
        return output

    def _run_test_script(self, filename='mytestscript.py',
                         interpreter='python'):
        env = {'PYTHONPATH': os.getcwd()}
        return subprocess.check_output([interpreter, self.tempdir + filename],
                                       env=env)


# Decorator to skip some tests on Python 2.6 ...
skip26 = unittest.skipIf(sys.version_info[:2] == (2, 6), "this test is known to fail on Py2.6")


# Renamed in Py3.3:
unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp
