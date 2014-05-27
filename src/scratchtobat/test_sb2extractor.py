import os
import tempfile
import unittest

from scratchtobat import common
from scratchtobat import common_testing
from scratchtobat import sb2
from scratchtobat import sb2extractor


class Sb2ExtractorTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.temp_dir = tempfile.mkdtemp()

    def test_can_extract_project(self):
        for project_file in common_testing.TEST_PROJECT_FILENAME_TO_ID_MAP:
            sb2extractor.extract_project(common.get_test_project_unpacked_file(project_file), self.temp_dir)
            self.assertTrue(sb2.Project(self.temp_dir))

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        common.rmtree(self.temp_dir)
        assert not os.path.exists(self.temp_dir)

if __name__ == "__main__":
    unittest.main()
