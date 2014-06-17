#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2014 The Catrobat Team
#  (<http://developer.catrobat.org/credits>)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  An additional term exception under section 7 of the GNU Affero
#  General Public License, version 3, is available at
#  http://developer.catrobat.org/license_additional_term
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest

from scratchtobat import common
from scratchtobat import common_testing
from scratchtobat import scratch
from scratchtobat import scratchwebapi


class WebApiTest(common_testing.BaseTestCase):

    def test_can_download_complete_project_from_project_url(self):
        for project_url, project_id in common_testing.TEST_PROJECT_URL_TO_ID_MAP.iteritems():
            self._set_testresult_folder_subdir(project_id)
            result_folder_path = self._testresult_folder_path
            scratchwebapi.download_project(project_url, result_folder_path)
            self.assertTrue(scratch.Project(result_folder_path))

    def test_fail_on_wrong_url(self):
        for wrong_url in ['http://www.tugraz.at', 'http://www.ist.tugraz.at/', 'http://scratch.mit.edu/', 'http://scratch.mit.edu/projects']:
            with self.assertRaises(common.ScratchtobatError):
                scratchwebapi.download_project(wrong_url, None)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
