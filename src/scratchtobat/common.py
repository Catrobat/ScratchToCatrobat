import logging
import os
import sys
import hashlib
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
import contextlib

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("scratchtobat")

APPLICATION_NAME = "Scratch to Catrobat Converter"


def isList(obj):
    return isinstance(obj, list)


def get_project_base_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_test_resources_path():
    return os.path.join(get_project_base_path(), "test", "res")


def get_test_project_path(project_folder):
    return os.path.join(get_test_resources_path(), "sb2", project_folder)


def get_test_project_unpacked_file(sb2_file):
    return os.path.join(get_test_resources_path(), "sb2_unpacked", sb2_file)


def get_testoutput_path(output_path):
    output_path = os.path.join(get_project_base_path(), "testoutput", "catrobat", output_path)
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    return output_path


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


def md5_hash(input_path):
    with open(input_path, "rb") as fp:
        return hashlib.md5(fp.read()).hexdigest()
