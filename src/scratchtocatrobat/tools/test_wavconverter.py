#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2015 The Catrobat Team
#  (http://developer.catrobat.org/credits)
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
#  along with this program.  If not, see http://www.gnu.org/licenses/.
import os
import unittest

from scratchtocatrobat.tools import common_testing
from scratchtocatrobat.tools import wavconverter

_ENV_PATH = "PATH"


class WavConverterTest(common_testing.BaseTestCase):

    @classmethod
    def adpcm_wavfile_paths(cls):
        return cls.get_test_resources_paths("wav_adpcm")

    @classmethod
    def pcm_wavfile_paths(cls):
        return cls.get_test_resources_paths("wav_pcm")

    @classmethod
    def setUpClass(cls):
        assert len(cls.adpcm_wavfile_paths()) == 7
        assert len(cls.pcm_wavfile_paths()) == 2

    def test_fail_on_missing_sox_binary(self):
        saved_path_env = os.environ[_ENV_PATH]
        os.environ[_ENV_PATH] = ""
        dummy_wav = self.adpcm_wavfile_paths()[0]
        output_path = None
        try:
            wavconverter.is_android_compatible_wav(dummy_wav)
            self.fail("Expected exception 'EnvironmentError' not thrown")
        except EnvironmentError:
            try:
                output_path = wavconverter.convert_to_android_compatible_wav(dummy_wav)
                self.fail("Expected exception 'EnvironmentError' not thrown")
            except EnvironmentError:
                pass
            finally:
                if output_path is not None:
                    output_file_exists = os.path.exists(output_path)
                    if output_file_exists:
                        os.remove(output_path)
                    assert not output_file_exists
        finally:
            os.environ[_ENV_PATH] = saved_path_env

    def test_can_detect_android_incompatible_wav_file(self):
        for wav_path in self.adpcm_wavfile_paths():
            assert not wavconverter.is_android_compatible_wav(wav_path)

    def test_can_detect_android_compatible_wav_file(self):
        for wav_path in self.pcm_wavfile_paths():
            assert wavconverter.is_android_compatible_wav(wav_path)

    def test_can_convert_android_incompatible_to_compatible_wav_file(self):
        for wav_path in self.adpcm_wavfile_paths():
            assert not wavconverter.is_android_compatible_wav(wav_path)
            converted_wav_path = wavconverter.convert_to_android_compatible_wav(wav_path)
            assert wavconverter.is_android_compatible_wav(converted_wav_path)
            os.remove(converted_wav_path)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

