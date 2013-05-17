import os
import unittest
import testing_common

from scratchreader import ScratchReader
from scratchreader import ScratchReaderException

class TestScratchReaderInitialization(unittest.TestCase):
    def test_can_create_reader_from_correct_json_file(self):
        json_file = os.path.join(testing_common.get_json_path() ,  "simple/project.json")
        scratch_reader = ScratchReader(json_file)
        self.assertTrue(scratch_reader, "No reader object")

    def test_can_detect_corrupt_sb2_json_file_with_reader(self):
        json_file = os.path.join(testing_common.get_json_path() ,  "wrong/project.json")
        with self.assertRaises(ScratchReaderException):
            ScratchReader(json_file)


class TestScratchReaderFunctionality(unittest.TestCase):
    def setUp(self):
        json_file = os.path.join(testing_common.get_json_path() ,  "simple/project.json")
        self.scratch_reader = ScratchReader(json_file)

    def test_can_read_sb2_json(self):
        json_dict = self.scratch_reader.get_dict()
        self.assertEquals(json_dict["objName"], "Stage")
        self.assertTrue(json_dict["info"])


if __name__ == '__main__':
    unittest.main()
