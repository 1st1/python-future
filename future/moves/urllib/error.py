from __future__ import absolute_import
from future.standard_library import suspend_hooks

# We use this method to get at the original Py2 urllib before any renaming magic
# ContentTooShortError = sys.py2_modules['urllib'].ContentTooShortError

with suspend_hooks():
    from urllib import ContentTooShortError
    from urllib2 import URLError, HTTPError
