#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2014 The Catrobat Team
#  (<http://developer.catrobat.org/credits>)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  An additional term exception under section 7 of the GNU Affero
#  General Public License, version 3, is available at
#  http://developer.catrobat.org/license_additional_term
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
import contextlib
import hashlib
import logging
import os
import shutil
import sys
import tempfile
try:
    from cStringIO import StringIO  # @UnusedImport (pydev problem 1/2)
except:
    from StringIO import StringIO  # @Reimport (pydev problem 2/2)
from datetime import datetime
from itertools import chain
from itertools import repeat
from itertools import islice


def get_project_base_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

log = logging.getLogger("scratchtobat")
log.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")

fh = logging.FileHandler(os.path.join(tempfile.gettempdir(), "scratchtobat-{}.log".format(datetime.now().isoformat().replace(":", "_"))))
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
log.addHandler(ch)

log.debug("Logging initialized")

APPLICATION_NAME = "Scratch to Catrobat Converter"


def isList(obj):
    return isinstance(obj, list)


def get_test_resources_path():
    return os.path.join(get_project_base_path(), "test", "res")


def get_test_project_path(project_folder):
    return os.path.join(get_test_resources_path(), "sb2", project_folder)


def get_test_project_unpacked_file(sb2_file):
    return os.path.join(get_test_resources_path(), "sb2_unpacked", sb2_file)


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


def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


# WORKAROUND: as shutil.rmtree fails on Windows with Jython for unknown reason with OSError (unlink())
def rmtree(path):
    assert os.path.exists(path)
    retry_count = 0
    while True:
        try:
            shutil.rmtree(path)
            if retry_count != 0:
                log.warning("Number of retries until path delete success: %d", retry_count)
            break
        except OSError:
            retry_count += 1
            if retry_count > 1000:
                log.warning("Could not delete: '%s' (trys: %d)", path, retry_count)
                break
            if not os.path.exists(path):
                break


# source for pad methods: http://stackoverflow.com/a/3438986
def pad_infinite(iterable, padding=None):
    return chain(iterable, repeat(padding))


def pad(iterable, size, padding=None):
    return islice(pad_infinite(iterable, padding), size)


class DictAccessWrapper(object):
    def __init__(self, dict_object):
        if isinstance(dict_object, set):
            dict_object = dict.fromkeys(dict_object, None)
        assert isinstance(dict_object, dict)
        self.__dict_object = dict_object

    def _checked_dict_access(self):
        dict_ = self._dict_access_object()
        assert isinstance(dict_, dict)
        return dict_

    def __getattr__(self, name):
        key = list(pad(name.split("_", 2), 2))[1]
        if name.startswith("get_"):
            return lambda: self.__dict_object.get(key)
        elif name.startswith("contains_"):
            return lambda: key in self.__dict_object
        else:
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, name))

    def __try_wrapped_access(self, key):
        try:
            return self.__dict_object[key]
        except KeyError:
            raise KeyError("Key '{}' is not available for '{}'. Available keys: {}".format(key, self, self.__dict_object.keys()))

    def __getitem__(self, key):
        return self.__try_wrapped_access(key)
