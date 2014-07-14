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
import hashlib
import logging
import os
import socket
import sys
import tempfile
import time
import urllib2
from datetime import datetime
from functools import wraps
from itertools import chain
from itertools import repeat
from itertools import islice

import java.lang.Class
from javax.sound.sampled import AudioFormat
from javax.sound.sampled import AudioInputStream
from javax.sound.sampled import AudioSystem

from org.python.core import PyReflectedField


def get_project_base_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

log = logging.getLogger("scratchtocatrobat")
log.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")

fh = logging.FileHandler(os.path.join(os.getcwd(), "scratchtocatrobat-{}.log".format(datetime.now().isoformat().replace(":", "_"))))
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
log.addHandler(ch)

log.debug("Logging initialized")

APPLICATION_NAME = "ScratchToCatrobat Converter"


def isList(obj):
    return isinstance(obj, list)


def get_test_resources_path(*path_parts):
    return os.path.join(get_project_base_path(), "test", "res", *path_parts)


def get_test_project_path(*path_parts):
    return os.path.join(get_test_resources_path(), "scratch", *path_parts)


def get_test_project_packed_file(scratch_file):
    return os.path.join(get_test_resources_path(), "scratch_packed", scratch_file)


class ScratchtobatError(Exception):
    pass


def md5_hash(input_path):
    with open(input_path, "rb") as fp:
        return hashlib.md5(fp.read()).hexdigest()


def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


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
        def get():
            return self.__dict_object.get(key)

        def contains():
            return key in self.__dict_object

        key = list(pad(name.split("_", 2), 2))[1]
        if name.startswith("get_"):
            return get
        elif name.startswith("contains_"):
            return contains
        else:
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, name))

    def __try_wrapped_access(self, key):
        try:
            return self.__dict_object[key]
        except KeyError:
            raise KeyError("Key '{}' is not available for '{}'. Available keys: {}".format(key, self, self.__dict_object.keys()))

    def __getitem__(self, key):
        return self.__try_wrapped_access(key)


# from Python 3 based on: http://stackoverflow.com/a/19299884
class TemporaryDirectory(object):
    """Create and return a temporary directory.  This has the same
    behavior as mkdtemp but can be used as a context manager.  For
    example:

        with TemporaryDirectory() as tmpdir:
            ...

    Upon exiting the context, the directory and everything contained
    in it are removed.
    """

    import warnings as _warnings
    import os as _os

    def __init__(self, suffix="", prefix="tmp", dir_=None):
        self._closed = False
        self.name = None  # Handle mkdtemp raising an exception
        self.name = tempfile.mkdtemp(suffix, prefix, dir_)

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self.name)

    def __enter__(self):
        return self.name

    def cleanup(self, _warn=False):
        if self.name and not self._closed:
            try:
                self._rmtree(self.name)
            except (TypeError, AttributeError) as ex:
                # Issue #10188: Emit a warning on stderr
                # if the directory could not be cleaned
                # up due to missing globals
                if "None" not in str(ex):
                    raise
                sys.stderr.write("ERROR: {!r} while cleaning up {!r}".format(ex, self,))
                return
            self._closed = True
            if _warn:
                self._warn("Implicitly cleaning up {!r}".format(self), _warn.ResourceWarning)

    def __exit__(self, _exc, _value, _tb):
        self.cleanup()

    def __del__(self):
        # Issue a ResourceWarning if implicit cleanup needed
        self.cleanup(_warn=True)

    # XXX (ncoghlan): The following code attempts to make
    # this class tolerant of the module nulling out process
    # that happens during CPython interpreter shutdown
    # Alas, it doesn't actually manage it. See issue #10188
    _listdir = staticmethod(_os.listdir)
    _path_exists = staticmethod(_os.path.exists)
    _isdir = staticmethod(_os.path.isdir)
    _islink = staticmethod(_os.path.islink)
    _path_join = staticmethod(_os.path.join)
    _remove = staticmethod(_os.remove)
    _rmdir = staticmethod(_os.rmdir)
    _warn = _warnings.warn

    def _rmtree(self, path):
        # Essentially a stripped down version of shutil.rmtree.  We can't
        # use globals because they may be None'ed out at shutdown.
        for name in self._listdir(path):
            fullname = self._path_join(path, name)
            try:
                isdir = self._isdir(fullname) and not self._islink(fullname)
            except OSError:
                isdir = False
            if isdir:
                self._rmtree(fullname)
            else:
                try:
                    self._remove(fullname)
                except OSError:
                    pass
        try:
            self._rmdir(path)
        except OSError:
            pass
        assert not self._path_exists(path)


# based on: http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
def retry(ExceptionToCheck, tries=3, delay=1, backoff=1, hook=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while True:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck, e:
                    if mtries > 0:
                        if hook:
                            hook(e, mtries, mdelay)
                        time.sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff
                    else:
                        raise e

        return f_retry  # true decorator

    return deco_retry


def fields_of(java_class):
    assert isinstance(java_class, java.lang.Class)
    return [name for name, type_ in vars(java_class).iteritems() if isinstance(type_, PyReflectedField)]


def url_response_data(url, retries=3, hook=None, timeout=3, log=log):
    def retry_hook(exc, tries, delay):
        log.warning("  retrying after %s:'%s' in %f secs (remaining trys: %d)", type(exc).__name__, exc, delay, tries)
    if hook is None:
        hook = retry_hook
    log.info("Requesting web api url: {}".format(url))

#     @retry((urllib2.URLError, socket.timeout), tries=retries, hook=hook)
    @retry((socket.timeout), tries=retries, hook=hook)
    def request():
        return urllib2.urlopen(url, timeout=timeout).read()

    try:
        return request()
    except socket.timeout:
        # WORKAROUND: little more descriptive
        raise IOError("socket.timeout")


def content_of(path):
    with open(path) as f:
        return f.read()


def length_of_audio_file_in_msec(file_path):
    audioInputStream = AudioSystem.getAudioInputStream(java.io.File(file_path))
    format_ = audioInputStream.getFormat()
    frames = audioInputStream.getFrameLength()
    return int((float(frames) / format_.getFrameRate()) * 1000)

