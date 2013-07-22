"""
Tests for the future.standard_library_renames module
"""

from __future__ import absolute_import, unicode_literals, print_function
from future import standard_library_renames, six

import unittest


class TestStandardLibraryRenames(unittest.TestCase):
    def test_configparser(self):
        import configparser
    
    def test_copyreg(self):
        import copyreg

    def test_pickle(self):
        import pickle

    def test_profile(self):
        import profile
    
    def test_io(self):
        from io import StringIO
        s = StringIO('test')
        for method in ['next', 'read', 'seek', 'close']:
            self.assertTrue(hasattr(s, method))

    def test_queue(self):
        import queue
        heap = ['thing', 'another thing']
        queue.heapq.heapify(heap)
        self.assertEqual(heap, ['another thing', 'thing'])

    # 'markupbase': '_markupbase',

    def test_reprlib(self):
        import reprlib

    def test_socketserver(self):
        import socketserver

    def test_tkinter(self):
        import tkinter

    # '_winreg': 'winreg',

    def test_builtins(self):
        import builtins
        self.assertTrue(hasattr(builtins, 'tuple'))


unittest.main()
