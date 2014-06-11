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
import os
import re
import subprocess
from distutils.spawn import find_executable
from java.lang import System

from scratchtobat import common

_SOX_BINARY = "sox"
_SOX_OUTPUT_PCM_PATTERN = re.compile("Sample Encoding:.* PCM")
# WORKAROUND: jython + find_executable() leads to wrong result if ".exe" extension is missing
if System.getProperty("os.name").lower().startswith("win"):
    _SOX_BINARY += ".exe"
_sox_path = find_executable(_SOX_BINARY)
if not _sox_path or _sox_path == _SOX_BINARY:
    raise common.ScratchtobatError("Sox binary not found on system path. Please add.")
assert os.path.exists(_sox_path)


def is_android_compatible_wav(file_path):
    assert file_path and os.path.exists(file_path), file_path
    info_output = subprocess.check_output([_sox_path, "--info", file_path])
    return _SOX_OUTPUT_PCM_PATTERN.search(info_output) is not None


def convert_to_android_compatible_wav(input_path, output_path):
    subprocess.check_call([_sox_path, input_path, "-t", "wavpcm", "-e", "unsigned-integer", output_path])
