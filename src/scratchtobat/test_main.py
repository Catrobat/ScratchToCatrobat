from scratchtobat import main, common, common_testing
import os
import unittest
import zipfile
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO


class MainTest(common_testing.ScratchtobatTestCase):

    def test_can_provide_catroid_project_for_scratch_link(self):
        for idx, project_url in enumerate(common_testing.TEST_PROJECT_URL_TO_NAME_MAP):
            output_zip_path = os.path.join(common_testing.get_test_resources_path(), "output{}.zip".format(idx))
            return_val = main.scratchtobat_main([project_url, output_zip_path])
            self.assertEqual(main.EXIT_SUCCESS, return_val)
            self.assertCorrectZipFile(output_zip_path, common_testing.TEST_PROJECT_URL_TO_NAME_MAP[project_url])
            
    def test_can_provide_catroid_project_for_scratch_file(self):
        for idx, project_file in enumerate(common_testing.TEST_PROJECT_FILES_TO_NAME_MAP):
            output_zip_path = os.path.join(common_testing.get_test_resources_path(), "output{}.zip".format(idx))
            return_val = main.scratchtobat_main([common_testing.
                        get_test_project_unpacked_file(project_file), output_zip_path])
            self.assertEqual(main.EXIT_SUCCESS, return_val)
            self.assertCorrectZipFile(output_zip_path, common_testing.TEST_PROJECT_FILES_TO_NAME_MAP[project_file])


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
