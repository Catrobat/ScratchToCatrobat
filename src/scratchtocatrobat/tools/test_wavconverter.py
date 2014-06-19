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
import unittest

from scratchtocatrobat import common
from scratchtocatrobat import common_testing
from scratchtocatrobat.tools import wavconverter

_ENV_PATH = "PATH"


class WavConverterTest(common_testing.BaseTestCase):

    def test_fail_on_sox_executable_not_on_path(self):
        saved_path_env = os.environ[_ENV_PATH]
        os.environ[_ENV_PATH] = ""
        try:
            import scratchtocatrobat.tools.wavconverter  # @UnusedImport
        except common.ScratchtobatError:
            pass
        finally:
            os.environ[_ENV_PATH] = saved_path_env

    def test_can_detect_android_incompatible_wav_file(self):
        wav_dir = os.path.join(common.get_test_resources_path(), "wav_adpcm")
        for wav_path in [os.path.join(wav_dir, _) for _ in os.listdir(wav_dir)]:
            self.assert_(not wavconverter.is_android_compatible_wav(wav_path))

    def test_can_detect_android_compatible_wav_file(self):
        wav_dir = os.path.join(common.get_test_resources_path(), "wav_pcm")
        for wav_path in [os.path.join(wav_dir, _) for _ in os.listdir(wav_dir)]:
            self.assert_(wavconverter.is_android_compatible_wav(wav_path))

    def test_can_convert_android_incompatible_to_compatible_wav_file(self):
        wav_dir = os.path.join(common.get_test_resources_path(), "wav_adpcm")
        for wav_path in [os.path.join(wav_dir, _) for _ in os.listdir(wav_dir)]:
            assert not wavconverter.is_android_compatible_wav(wav_path)
            converted_wav_path = os.path.join(self._testresult_folder_path, os.path.basename(wav_path))
            wavconverter.convert_to_android_compatible_wav(wav_path, converted_wav_path)
            self.assert_(wavconverter.is_android_compatible_wav(converted_wav_path))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
