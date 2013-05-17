import os
import unittest
import testing_common

from scratchreader import ScratchReader
from scratchreader import ScratchReaderException
from catrobatwriter import CatrobatWriter

class TestCatrobatWriter(unittest.TestCase):

    def setUp(self):
        json_file = os.path.join(testing_common.get_json_path() , "simple/project.json")
        self.scratch_reader = ScratchReader(json_file)
        self.json_dict = self.scratch_reader.get_dict()

    def test_can_write_simple(self):
        catrobat_writer = CatrobatWriter(self.json_dict)
        catrobat_writer.process_dict()

        self.assertEquals(catrobat_writer.document.
        getElementsByTagName("applicationBuildNumber")[0].firstChild.nodeValue, "0")

        self.assertEquals(catrobat_writer.document.
        getElementsByTagName("screenHeight")[0].firstChild.nodeValue, "800")

        self.assertEquals(catrobat_writer.document.
        getElementsByTagName("screenWidth")[0].firstChild.nodeValue, "480")

        print catrobat_writer.document.toprettyxml()

    def test_can_get_media_files(self):
        catrobat_writer = CatrobatWriter(self.json_dict)
        catrobat_writer.process_dict()
        sound_files = catrobat_writer.sound_files
        costume_files = catrobat_writer.costume_files
        self.assertEquals(sound_files, ["83A9787D4CB6F3B7632B4DDFEBF74367_pop.wav",
                                                    "83C36D806DC92327B9E7049A565C6BFF_meow.wav"])

        self.assertEquals(costume_files, ["510DA64CF172D53750DFFD23FBF73563_backdrop1",
                                                    "F9A1C175DBE2E5DEE472858DD30D16BB_costume1",
                                                    "6E8BD9AE68FDB02B7E1E3DF656A75635_costume2"])

if __name__ == '__main__':
    unittest.main()
