import logging
import os
import sys
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
import contextlib

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("scratchtobat")


def isList(obj):
    return isinstance(obj, list)


def get_project_base_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


class Data(object):
    pass


@contextlib.contextmanager
def capture_stdout():
    old = sys.stdout
    capturer = StringIO()
    sys.stdout = capturer
    data = Data()
    yield data
    sys.stdout = old
    data.result = capturer.getvalue()


class ScratchtobatError(Exception):
    pass
