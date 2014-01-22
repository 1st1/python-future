"""
A module that brings in equivalents of various modified Python 3 builtins
into Py2. Has no effect on Py3.

The builtin functions are:

- ``ascii`` (from Py2's future_builtins module)
- ``hex`` (from Py2's future_builtins module)
- ``oct`` (from Py2's future_builtins module)
- ``chr`` (equivalent to ``unichr`` on Py2)
- ``input`` (equivalent to ``raw_input`` on Py2)
- ``open`` (equivalent to io.open on Py2)
- ``super`` (backport of Py3's magic zero-argument super() function
- ``round`` (new "Banker's Rounding" behaviour from Py3)


input()
-------
Like the new ``input()`` function from Python 3 (without eval()), except
that it returns bytes. Equivalent to Python 2's ``raw_input()``.

Warning: By default, importing this module *removes* the old Python 2
input() function entirely from ``__builtin__`` for safety. This is
because forgetting to import the new ``input`` from ``future`` might
otherwise lead to a security vulnerability (shell injection) on Python 2.

To restore it, you can retrieve it yourself from
``__builtin__._old_input``.

Fortunately, ``input()`` seems to be seldom used in the wild in Python
2...

"""

from future import utils


if utils.PY2:
    from io import open
    from future_builtins import ascii, oct, hex
    from __builtin__ import unichr as chr
    import __builtin__

    # Warning: Python 2's input() is unsafe and MUST not be able to be used
    # accidentally by someone who expects Python 3 semantics but forgets
    # to import it on Python 2. Versions of ``future`` prior to 0.11
    # deleted it from __builtin__.  Now we have reverted to the default
    # behaviour. Just be careful.

    input = raw_input

    from future.builtins.newround import newround as round
    from future.builtins.newsuper import newsuper as super

    # ``future`` doesn't support Py3.0/3.1. If we ever did, we'd add this:
    #     callable = __builtin__.callable

    __all__ = ['ascii', 'chr', 'hex', 'input', 'oct', 'open',
               'round', 'super']

else:
    import builtins
    ascii = builtins.ascii
    chr = builtins.chr
    hex = builtins.hex
    input = builtins.input
    oct = builtins.oct
    open = builtins.open
    round = builtins.round
    super = builtins.super

    __all__ = []

    # The callable() function was removed from Py3.0 and 3.1 and
    # reintroduced into Py3.2+. ``future`` doesn't support Py3.0/3.1. If we ever
    # did, we'd add this:
    # try:
    #     callable = builtins.callable
    # except AttributeError:
    #     # Definition from Pandas
    #     def callable(obj):
    #         return any("__call__" in klass.__dict__ for klass in type(obj).__mro__)
    #     __all__.append('callable')
