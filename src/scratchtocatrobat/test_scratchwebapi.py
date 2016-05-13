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
import os

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

TEST_PROJECT_ID_TO_REMIXES_MAP = {
    "10205819": [{
        'owner': 'Amanda69',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/10211023_144x108.png?v=1368486334.0',
        'title': "Dancin' in the Castle remake"
    }],
    "10132588": []
}

TEST_PROJECT_ID_TO_TAGS_MAP = {
    "10205819": ['animations', 'castle'],
    "10132588": ['music', 'simulations', 'animations']
}

TEST_PROJECT_ID_TO_INSTRUCTIONS_MAP = {
    "10205819": "Click the flag to run the stack. Click the space bar to change it up!",
    "10132588": "D,4,8 for the animals to move.C,A for background."
}

TEST_PROJECT_ID_TO_NOTES_AND_CREDITS_MAP = {
    "10205819": "First project on Scratch! This was great.",
    "10132588": ""
}

class WebApiTest(common_testing.BaseTestCase):

    def test_can_download_project_from_project_url(self):
        for project_url, project_id in common_testing.TEST_PROJECT_URL_TO_ID_MAP.iteritems():
            self._set_testresult_folder_subdir(project_id)
            result_folder_path = self._testresult_folder_path
            scratchwebapi.download_project(project_url, result_folder_path)
            # TODO: replace with verifying function
            assert scratch.Project(result_folder_path) is not None

    def test_fail_download_project_on_wrong_url(self):
        for wrong_url in ['http://www.tugraz.at', 'http://www.ist.tugraz.at/', 'http://scratch.mit.edu/', 'http://scratch.mit.edu/projects']:
            with self.assertRaises(scratchwebapi.ScratchWebApiError):
                scratchwebapi.download_project(wrong_url, None)

    def test_can_request_project_code_for_id(self):
        with common.TemporaryDirectory(remove_on_exit=True) as temp_dir:
            for _project_url, project_id in common_testing.TEST_PROJECT_URL_TO_ID_MAP.iteritems():
                scratchwebapi.download_project_code(project_id, temp_dir)
                project_file_path = os.path.join(temp_dir, scratch._PROJECT_FILE_NAME)
                with open(project_file_path, 'r') as project_code_file:
                    project_code_content = project_code_file.read()
                    raw_project = scratch.RawProject.from_project_code_content(project_code_content)
                    assert raw_project is not None

    def test_can_request_project_title_for_id(self):
        for (project_id, expected_project_title) in TEST_PROJECT_ID_TO_TITLE_MAP.iteritems():
            extracted_project_title = scratchwebapi.request_project_title_for(project_id)
            assert extracted_project_title is not None
            assert extracted_project_title == expected_project_title, \
                   "'{}' is not equal to '{}'".format(extracted_project_title, expected_project_title)

    def test_can_request_project_owner_for_id(self):
        for (project_id, expected_project_owner) in TEST_PROJECT_ID_TO_OWNER_MAP.iteritems():
            extracted_project_owner = scratchwebapi.request_project_owner_for(project_id)
            assert extracted_project_owner is not None
            assert extracted_project_owner == expected_project_owner, \
                   "'{}' is not equal to '{}'".format(extracted_project_owner, expected_project_owner)

    def test_can_request_project_instructions_for_id(self):
        for (project_id, expected_project_instructions) in TEST_PROJECT_ID_TO_INSTRUCTIONS_MAP.iteritems():
            extracted_project_instructions = scratchwebapi.request_project_instructions_for(project_id)
            assert extracted_project_instructions is not None
            assert extracted_project_instructions == expected_project_instructions, \
                   "'{}' is not equal to '{}'".format(extracted_project_instructions, expected_project_instructions)

    def test_can_request_project_notes_and_credits_for_id(self):
        for (project_id, expected_project_notes_and_credits) in TEST_PROJECT_ID_TO_NOTES_AND_CREDITS_MAP.iteritems():
            extracted_project_notes_and_credits = scratchwebapi.request_project_notes_and_credits_for(project_id)
            assert extracted_project_notes_and_credits is not None
            assert extracted_project_notes_and_credits == expected_project_notes_and_credits, \
                   "'{}' is not equal to '{}'".format(extracted_project_notes_and_credits, expected_project_notes_and_credits)

    def test_can_request_remixes_for_id(self):
        for (project_id, expected_project_remixes) in TEST_PROJECT_ID_TO_REMIXES_MAP.iteritems():
            extracted_project_remixes = scratchwebapi.request_project_remixes_for(project_id)
            assert extracted_project_remixes is not None
            assert extracted_project_remixes == expected_project_remixes, \
                   "'{}' is not equal to '{}'".format(extracted_project_remixes, expected_project_remixes)

    def test_can_request_project_info_for_id(self):
        for (project_id, expected_project_title) in TEST_PROJECT_ID_TO_TITLE_MAP.iteritems():
            extracted_project_info = scratchwebapi.request_project_details_for(project_id)
            assert extracted_project_info is not None
            assert isinstance(extracted_project_info, scratchwebapi.ScratchProjectInfo)
            assert extracted_project_info.title is not None
            assert extracted_project_info.title == expected_project_title, \
                   "'{}' is not equal to '{}'".format(extracted_project_info.title, expected_project_title)
            assert extracted_project_info.owner is not None
            assert extracted_project_info.owner == TEST_PROJECT_ID_TO_OWNER_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(extracted_project_info.owner, TEST_PROJECT_ID_TO_OWNER_MAP[project_id])
            assert extracted_project_info.instructions is not None
            assert extracted_project_info.instructions == TEST_PROJECT_ID_TO_INSTRUCTIONS_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(extracted_project_info.owner, TEST_PROJECT_ID_TO_INSTRUCTIONS_MAP[project_id])
            assert extracted_project_info.notes_and_credits is not None
            assert extracted_project_info.notes_and_credits == TEST_PROJECT_ID_TO_NOTES_AND_CREDITS_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(extracted_project_info.owner, TEST_PROJECT_ID_TO_NOTES_AND_CREDITS_MAP[project_id])
            assert extracted_project_info.tags is not None
            assert extracted_project_info.tags == TEST_PROJECT_ID_TO_TAGS_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(extracted_project_info.tags, TEST_PROJECT_ID_TO_TAGS_MAP[project_id])
            assert extracted_project_info.views is not None
            assert isinstance(extracted_project_info.views, int)
            assert extracted_project_info.views > 0
            assert extracted_project_info.favorites is not None
            assert extracted_project_info.favorites >= 0
            assert isinstance(extracted_project_info.favorites, int)
            assert extracted_project_info.loves is not None
            assert extracted_project_info.loves >= 0
            assert isinstance(extracted_project_info.loves, int)
            assert extracted_project_info.modified_date is not None
            assert isinstance(extracted_project_info.modified_date, (str, unicode))
            assert extracted_project_info.shared_date is not None
            assert isinstance(extracted_project_info.shared_date, (str, unicode))
            assert extracted_project_info.remixes is not None
            assert extracted_project_info.remixes == TEST_PROJECT_ID_TO_REMIXES_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(extracted_project_info.remixes, TEST_PROJECT_ID_TO_REMIXES_MAP[project_id])
            assert isinstance(extracted_project_info.remixes, list)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
