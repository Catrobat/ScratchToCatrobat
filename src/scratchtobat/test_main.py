import os
import unittest

from scratchtobat import common
from scratchtobat import common_testing
from scratchtobat import main


class MainTest(common_testing.ProjectTestCase):

    def __init__(self, *args):
        super(MainTest, self).__init__(*args)
        self._main_method = main.scratchtobat_main

    def setUp(self):
        super(MainTest, self).setUp()

    def assertMainSuccess(self, args, project_id):
        if len(args) == 1:
            args += [self._testresult_folder_path]
        return_val = self._main_method(args)
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
