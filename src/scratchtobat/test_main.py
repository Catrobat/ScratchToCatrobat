from scratchtobat import main, common, common_testing
import unittest
import os
import shutil


class MainTest(common_testing.ProjectTestCase):

    def assert_main_success(self, args, project_name):
            output_zip_dir = common.get_testoutput_path("output_zips")
            return_val = main.scratchtobat_main(args)
            self.assertEqual(main.EXIT_SUCCESS, return_val)
            for file_ in os.listdir(output_zip_dir):
                if file_.endswith(".zip"):
                    zip_path = os.path.join(file_)
                    self.assertCorrectZipFile(zip_path, project_name)
            shutil.rmtree(output_zip_dir)

    def test_can_provide_catroid_project_for_scratch_link(self):
        for project_url, project_name in common_testing.TEST_PROJECT_URL_TO_NAME_MAP.iteritems():
            output_zip_dir = common.get_testoutput_path("output_zips")
            self.assert_main_success([project_url, output_zip_dir], project_name)

    def test_can_provide_catroid_project_for_scratch_file(self):
        for project_file, project_name in common_testing.TEST_PROJECT_FILES_TO_NAME_MAP.iteritems():
            output_zip_dir = common.get_testoutput_path("output_zips")
            self.assert_main_success([common.get_test_project_unpacked_file(project_file), output_zip_dir], project_name)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
