import os
import unittest
import testing_common

from scratchreader import ScratchReader
from scratchreader import ScratchReaderException 

class TestScratchReader(unittest.TestCase):
    def setUp(self):
        pass
        
    def test_can_read_sb2_json(self):
        json_file = os.path.join(testing_common.get_json_path() ,  "simple/project.json") 
        #~ print json_file
                                          
        scratch_reader = ScratchReader(json_file)
        json_dict = scratch_reader.get_dict()
        
        self.assertEquals(json_dict["objName"], "Stage")
        self.assertTrue(json_dict["info"])

    def test_can_detect_corrupt_sb2_json_file(self):
        json_file = os.path.join(testing_common.get_json_path() ,  "wrong/project.json")
        with self.assertRaises(ScratchReaderException): 
            ScratchReader(json_file)
    
    
    
if __name__ == '__main__':
    unittest.main()
    