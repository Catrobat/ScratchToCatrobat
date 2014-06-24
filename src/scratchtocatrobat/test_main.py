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
import os
import unittest

from scratchtocatrobat import common
from scratchtocatrobat import common_testing
from scratchtocatrobat import main


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

    def test_can_provide_catrobat_program_for_scratch_project_link(self):
        for project_url, project_id in common_testing.TEST_PROJECT_URL_TO_ID_MAP.iteritems():
            self.assertMainSuccess([project_url], project_id)

    def test_can_provide_catrobat_program_for_scratch_project_file(self):
        for project_filename, project_id in common_testing.TEST_PROJECT_FILENAME_TO_ID_MAP.iteritems():
            self.assertMainSuccess([common.get_test_project_packed_file(project_filename)], project_id)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
