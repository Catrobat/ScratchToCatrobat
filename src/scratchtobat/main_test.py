import unittest
from scratchtobat import main, common, testing_common
import os
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
import zipfile


class MainTest(unittest.TestCase):

    def test_can_provide_catroid_project_for_scratch_link(self):
        for idx, project_url in enumerate(testing_common.TEST_PROJECT_URLS):
            output_zip_path = os.path.join(testing_common.get_test_resources_path(), "output{}.zip".format(idx))
            with common.capture_stdout() as capture:
                main.scratchtobat_main([project_url, output_zip_path])
            with open(output_zip_path, "rb") as fp:
                zip_file = zipfile.ZipFile(fp)
                self.assertTrue(zip_file.testzip())


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
