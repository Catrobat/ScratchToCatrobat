import os
import unittest

from scratchtobat import common
from scratchtobat import common_testing
from scratchtobat import main


class MainTest(common_testing.ProjectTestCase):

    def setUp(self):
        common_testing.ProjectTestCase.setUp(self)

    def assertMainSuccess(self, args, project_id):
        output_path = os.path.join(self._testcase_result_folder_path, project_id)
        common.makedirs(output_path)
        if len(args) == 1:
            args += [output_path]
        return_val = main.scratchtobat_main(args)
        self.assertEqual(main.EXIT_SUCCESS, return_val)
        test_folder_path = args[1]
        for file_ in os.listdir(test_folder_path):
            if file_.endswith(".zip"):
                zip_path = os.path.join(file_)
                self.assertCorrectProjectZipFile(zip_path, project_id)

    def test_can_provide_catroid_project_for_scratch_link(self):
        for project_url, project_id in common_testing.TEST_PROJECT_URL_TO_ID_MAP.iteritems():
            self.assertMainSuccess([project_url], project_id)

    def test_can_provide_catroid_project_for_scratch_file(self):
        for project_filename, project_id in common_testing.TEST_PROJECT_FILENAME_TO_ID_MAP.iteritems():
            self.assertMainSuccess([common.get_test_project_unpacked_file(project_filename)], project_id)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
