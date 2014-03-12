"""
Tests to make sure the newobject object (which defines Python 2-compatible
``__unicode__`` and ``next`` methods) is working.
"""

from __future__ import absolute_import, division
from future import utils
from future.builtins import object, str, next, int, super
from future.utils import implements_iterator, python_2_unicode_compatible
from future.tests.base import unittest


class TestNewObject(unittest.TestCase):
    def test_object_implements_py2_unicode_method(self):
        my_unicode_str = u'Unicode string: \u5b54\u5b50'
        class A(object):
            def __str__(self):
                return my_unicode_str
        a = A()
        self.assertEqual(len(str(a)), 18)
        if utils.PY2:
            self.assertTrue(hasattr(a, '__unicode__'))
        else:
            self.assertFalse(hasattr(a, '__unicode__'))
        self.assertEqual(str(a), my_unicode_str)
        self.assertTrue(isinstance(str(a).encode('utf-8'), bytes))
        if utils.PY2:
            self.assertTrue(type(unicode(a)) == unicode)
            self.assertEqual(unicode(a), my_unicode_str)

        # Manual equivalent on Py2 without the decorator:
        if not utils.PY3:
            class B(object):
                def __unicode__(self):
                    return u'Unicode string: \u5b54\u5b50'
                def __str__(self):
                    return unicode(self).encode('utf-8')
            b = B()
            assert str(a) == str(b)

    def test_implements_py2_iterator(self):
        
        class Upper(object):
            def __init__(self, iterable):
                self._iter = iter(iterable)
            def __next__(self):                 # note the Py3 interface
                return next(self._iter).upper()
            def __iter__(self):
                return self

        self.assertEqual(list(Upper('hello')), list('HELLO'))

        # Try combining it with the next() function:

        class MyIter(object):
            def __next__(self):
                return 'Next!'
            def __iter__(self):
                return self
        
        itr = MyIter()
        self.assertEqual(next(itr), 'Next!')

        itr2 = MyIter()
        for i, item in enumerate(itr2):
            if i >= 10:
                break
            self.assertEqual(item, 'Next!')

    def test_implements_py2_nonzero(self):
        
        class EvenIsTrue(object):
            """
            An integer that evaluates to True if even.
            """
            def __init__(self, my_int):
                self.my_int = my_int
            def __bool__(self):
                return self.my_int % 2 == 0
            def __add__(self, other):
                return type(self)(self.my_int + other)

        k = EvenIsTrue(5)
        self.assertFalse(k)
        self.assertFalse(bool(k))
        self.assertTrue(k + 1)
        self.assertTrue(bool(k + 1))
        self.assertFalse(k + 2)


    def test_int_implements_py2_nonzero(self):
        """
        Tests whether the newint object provides a __nonzero__ method that
        maps to __bool__ in case the user redefines __bool__ in a subclass of
        newint.
        """
        
        class EvenIsTrue(int):
            """
            An integer that evaluates to True if even.
            """
            def __bool__(self):
                return self % 2 == 0
            def __add__(self, other):
                val = super().__add__(other)
                return type(self)(val)

        k = EvenIsTrue(5)
        self.assertFalse(k)
        self.assertFalse(bool(k))
        self.assertTrue(k + 1)
        self.assertTrue(bool(k + 1))
        self.assertFalse(k + 2)

    def test_non_iterator(self):
        """
        The default behaviour of next(o) for a newobject o should be to raise a
        TypeError, as with the corresponding builtin object.
        """
        o = object()
        with self.assertRaises(TypeError):
            next(o)

    def test_bool_empty_object(self):
        """
        The default result of bool(newobject()) should be True, as with builtin
        objects.
        """
        o = object()
        self.assertTrue(bool(o))

        class MyClass(object):
            pass

        obj = MyClass()
        self.assertTrue(bool(obj))


if __name__ == '__main__':
    unittest.main()
