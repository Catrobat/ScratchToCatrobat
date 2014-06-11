import os
import sndhdr
import subprocess
from contextlib import closing
from distutils.spawn import find_executable
from java.lang import System

from scratchtobat import common
from scratchtobat.tools.internal import wave

_SOX_BINARY = "sox"
# WORKAROUND: jython + find_executable() leads to wrong result if ".exe" extension is missing
if System.getProperty("os.name").lower().startswith("win"):
    _SOX_BINARY += ".exe"


def is_android_compatible_wav(file_path):
    assert file_path and os.path.exists(file_path), file_path
    header = sndhdr.whathdr(file_path)
    is_wav = header and header[0] == 'wav'
    if is_wav:
        try:
            with closing(wave.open(file_path)) as fp:
                return fp.getcomptype() == 'NONE'
        except wave.Error:
            # HACK: as wave module only supports uncompressed files, compressed wav files raise exceptions
            return False

    return False


def convert_to_android_compatible_wav(input_path, output_path):

    sox_path = find_executable(_SOX_BINARY)
    if not sox_path or sox_path == _SOX_BINARY:
        raise common.ScratchtobatError("Sox binary not found on system path. Please add.")

    assert os.path.exists(sox_path)

    def get_sox_arguments(input_filepath, output_filepath):
        return [input_filepath, "-t", "wavpcm", "-e", "unsigned-integer", output_filepath]
    subprocess.call([sox_path] + get_sox_arguments(input_path, output_path))
