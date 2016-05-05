#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2015 The Catrobat Team
#  (http://developer.catrobat.org/credits)
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
#  along with this program.  If not, see http://www.gnu.org/licenses/.
import unittest

from scratchtocatrobat import common
from scratchtocatrobat import common_testing
from scratchtocatrobat import scratch
from scratchtocatrobat import scratchwebapi

TEST_PROJECT_ID_TO_TITLE_MAP = {
    "10205819": "Dancin' in the Castle",
    "10132588": "Dance back"
}

TEST_PROJECT_ID_TO_OWNER_MAP = {
    "10205819": "jschombs",
    "10132588": "psush09"
}

TEST_PROJECT_ID_TO_DESCRIPTION_MAP = {
    "10205819": "----------------------------------------\n" \
                + "Instructions:\nClick the flag to run the stack. Click the space bar to change it up!\n"
                + "--------------------------------------------------------------------------------\n"
                + "Description:\nFirst project on Scratch! This was great.\n"
                + "----------------------------------------",
    "10132588": "----------------------------------------\n" \
                + "Instructions:\nD,4,8 for the animals to move.C,A for background.\n"
                + "--------------------------------------------------------------------------------\n"
                + "Description:\n\n----------------------------------------",
}

class WebApiTest(common_testing.BaseTestCase):

    def test_can_download_complete_project_from_project_url(self):
        for project_url, project_id in common_testing.TEST_PROJECT_URL_TO_ID_MAP.iteritems():
            self._set_testresult_folder_subdir(project_id)
            result_folder_path = self._testresult_folder_path
            scratchwebapi.download_project(project_url, result_folder_path)
            # TODO: replace with verifying function
            assert scratch.Project(result_folder_path)

    def test_fail_on_wrong_url(self):
        for wrong_url in ['http://www.tugraz.at', 'http://www.ist.tugraz.at/', 'http://scratch.mit.edu/', 'http://scratch.mit.edu/projects']:
            with self.assertRaises(common.ScratchtobatError):
                scratchwebapi.download_project(wrong_url, None)

    def test_can_request_project_code_content(self):
        for _project_url, project_id in common_testing.TEST_PROJECT_URL_TO_ID_MAP.iteritems():
            # TODO: fix tests!
            pass
            #project_code = scratchwebapi.request_project_code(project_id)
            #raw_project = scratch.RawProject.from_project_code_content(project_code)
            #assert raw_project

    def test_can_request_project_title_for_id(self):
        for (project_id, expected_project_title) in TEST_PROJECT_ID_TO_TITLE_MAP.iteritems():
            extracted_project_title = scratchwebapi.request_project_title_for(project_id)
            assert extracted_project_title is not None
            assert extracted_project_title == expected_project_title, \
                   "'{}' is not equal to '{}'".format(extracted_project_title, expected_project_title)

    def test_can_request_project_owner_for_id(self):
        for (project_id, expected_project_owner) in TEST_PROJECT_ID_TO_OWNER_MAP.iteritems():
            document = scratchwebapi.request_project_page_as_Jsoup_document_for(project_id)
            extracted_project_owner = scratchwebapi.extract_project_owner_from_document(document)
            assert extracted_project_owner is not None
            assert extracted_project_owner == expected_project_owner, \
                   "'{}' is not equal to '{}'".format(extracted_project_owner, expected_project_owner)

    def test_can_request_project_description_for_id(self):
        for (project_id, expected_project_description) in TEST_PROJECT_ID_TO_DESCRIPTION_MAP.iteritems():
            extracted_project_description = scratchwebapi.request_project_description_for(project_id)
            assert extracted_project_description is not None
            assert extracted_project_description == expected_project_description, \
                   "'{}' is not equal to '{}'".format(extracted_project_description, expected_project_description)

    def test_can_request_project_info_for_id(self):
        for (project_id, expected_project_title) in TEST_PROJECT_ID_TO_TITLE_MAP.iteritems():
            document = scratchwebapi.request_project_page_as_Jsoup_document_for(project_id)
            assert document is not None
            extracted_project_info = scratchwebapi.extract_project_details_from_document(document)
            assert extracted_project_info is not None
            assert isinstance(extracted_project_info, scratchwebapi.ScratchProjectInfo)
            assert extracted_project_info.title is not None
            assert extracted_project_info.title == expected_project_title, \
                   "'{}' is not equal to '{}'".format(extracted_project_info.title, expected_project_title)
            assert extracted_project_info.owner is not None
            assert extracted_project_info.owner == TEST_PROJECT_ID_TO_OWNER_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(extracted_project_info.owner, TEST_PROJECT_ID_TO_OWNER_MAP[project_id])
            assert extracted_project_info.description is not None
            assert extracted_project_info.description == TEST_PROJECT_ID_TO_DESCRIPTION_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(extracted_project_info.owner, TEST_PROJECT_ID_TO_DESCRIPTION_MAP[project_id])
            assert extracted_project_info.views is not None
            assert isinstance(extracted_project_info.views, int)
            assert extracted_project_info.views > 0
            assert extracted_project_info.favorites is not None
            assert extracted_project_info.favorites >= 0
            assert isinstance(extracted_project_info.favorites, int)
            assert extracted_project_info.loves is not None
            assert extracted_project_info.loves >= 0
            assert isinstance(extracted_project_info.loves, int)
            assert extracted_project_info.remixes is not None
            assert isinstance(extracted_project_info.remixes, list)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
