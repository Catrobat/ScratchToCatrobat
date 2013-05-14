import os
import unittest
import testing_common

from scratchreader import ScratchReader
from scratchreader import ScratchReaderException 
from catrobatwriter import CatrobatWriter

class TestCatrobatWriter(unittest.TestCase):
    def setUp(self):
        pass
        
    def test_can_write_simple(self):
        json_file = os.path.join(testing_common.get_json_path() ,  "simple/project.json") 
                                          
        scratch_reader = ScratchReader(json_file)
        json_dict = scratch_reader.get_dict()
        
        self.assertEquals(json_dict["objName"], "Stage")
        self.assertTrue(json_dict["info"])
        
        catrobat_writer = CatrobatWriter(json_dict)
        catrobat_writer.process_dict()
        self.assertEquals(catrobat_writer.document.
        getElementsByTagName("applicationBuildNumber")[0].firstChild.nodeValue, "0")
        
        print catrobat_writer.document.toxml()

    
if __name__ == '__main__':
    unittest.main()
    