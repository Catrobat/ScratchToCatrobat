import unittest

from scratchtobat import common
from scratchtobat import common_testing
from scratchtobat import sb2
from scratchtobat import sb2webapi


class WebApiTest(common_testing.BaseTestCase):

    def test_can_download_complete_project_from_project_url(self):
        for project_url, project_id in common_testing.TEST_PROJECT_URL_TO_ID_MAP.iteritems():
            self._set_testresult_folder_subdir(project_id)
            result_folder_path = self._testresult_folder_path
            sb2webapi.download_project(project_url, result_folder_path)
            self.assertTrue(sb2.Project(result_folder_path))

    def test_fail_on_wrong_url(self):
        for wrong_url in ['http://www.tugraz.at', 'http://www.ist.tugraz.at/', 'http://scratch.mit.edu/', 'http://scratch.mit.edu/projects']:
            with self.assertRaises(common.ScratchtobatError):
                sb2webapi.download_project(wrong_url, None)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
