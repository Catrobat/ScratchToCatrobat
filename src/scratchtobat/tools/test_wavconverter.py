from scratchtobat import common
from scratchtobat.common_testing import BaseTestCase
from scratchtobat.tools import wavconverter
import os
import unittest


class WavConverterTest(BaseTestCase):

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
            converted_wav_path = os.path.join(self.temp_dir, os.path.basename(wav_path))
            wavconverter.convert_to_android_compatible_wav(wav_path, converted_wav_path)
            self.assert_(wavconverter.is_android_compatible_wav(converted_wav_path))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
