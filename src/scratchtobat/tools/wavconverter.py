from contextlib import closing
from scratchtobat import common
from scratchtobat.tools.internal import wave
import os
import sndhdr
import subprocess

_ENV_SOX_HOME = "SOX_HOME"
_SOX_BINARY = "sox"


def is_android_compatible_wav(file_path):
    assert file_path and os.path.exists(file_path), file_path
    header = sndhdr.whathdr(file_path)
    is_wav = header and header[0] == 'wav'
    if is_wav:
        try:
            with closing(wave.open(file_path)) as fp:
                return fp.getcomptype() == 'NONE'
        except wave.Error:
            # as only uncompressed are supported, compressed wav files raise exceptions
            return False

    return False



def convert_to_android_compatible_wav(input_path, output_path):
    def get_sox_arguments(input_filepath, output_filepath):
        return [input_filepath, "-t", "wavpcm", "-e", "unsigned-integer", output_filepath]

    sox_home_dir = os.environ.get(_ENV_SOX_HOME)
    if not sox_home_dir:
        raise common.ScratchtobatError("Environment variable '{}' not found. Please specify.".format(_ENV_SOX_HOME))

    sox_path = os.path.join(sox_home_dir, _SOX_BINARY)
    if not os.path.exists(sox_path):
        subprocess.call([sox_path] + get_sox_arguments(input_path, output_path))
