# -*- coding: utf-8 -*-
#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2017 The Catrobat Team
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

from scratchtocatrobat.tools import common, common_testing
from scratchtocatrobat.scratch import scratch, scratchwebapi, scratch3
from datetime import datetime

TEST_PROJECT_ID_TO_TITLE_MAP = {
    "390300019": "Dancin' in the Castle",
    "390299427": "Dance back",
    "390300655": u"Fußball Kapfenstein",
    "390300756": u"やねうら部屋（びっくりハウス）"
}

TEST_PROJECT_ID_TO_IMAGE_URL_MAP = {
    "390300019": "https://cdn2.scratch.mit.edu/get_image/project/390300019_480x360.png",
    "390299427": "https://cdn2.scratch.mit.edu/get_image/project/390299427_480x360.png",
    "390300655" : "https://cdn2.scratch.mit.edu/get_image/project/390300655_480x360.png",
    "390300756": "https://cdn2.scratch.mit.edu/get_image/project/390300756_480x360.png"
}

TEST_PROJECT_ID_TO_OWNER_MAP = {
    "390300019": "stccaa",
    "390299427": "stccaa",
    "390300655" : "stccaa",
    "390300756": "stccaa"
}

TEST_PROJECT_ID_TO_REMIXES_MAP = {
    "390300019": [{
        'id'   : 394233634,
        'owner': u's2cc',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/394233634.png',
        'title': "Dancin' in the Castle remake"
    }],
    "390299427": [],
    "390300655": [],
    "390300756": []
}

TEST_PROJECT_ID_TO_INSTRUCTIONS_MAP = {
    "390300019": "Click the flag to run the stack. Click the space bar to change it up!",
    "390299427": "D,4,8 for the animals to move.C,A for background. ",
    "390300655" : "",
    "390300756": u"◆「Why!?大喜利」8月のお題\n・キミのびっくりハウスをつくろう！～やねうら部屋 編～\n\n" \
                 u"広い“屋根裏部屋”には、何もないみたいだね。好きなものを書いたり、おいたりして“びっく" \
                 u"り”を作ろう。スプライトには助っ人として、マックスとリンゴがあるぞ！\n\n" \
                 u"◆自由にリミックス（改造）して、遊んでください！\n面白い作品ができたら、こちらまで投稿を！\nhttp://www.nhk." \
                 u"or.jp/xxx\n※リミックス作品を投稿する時は”共有”を忘れないでね。\n"
}

TEST_PROJECT_ID_TO_NOTES_AND_CREDITS_MAP = {
    "390300019": "First project on Scratch! This was great.",
    "390299427": "",
    "390300655" : "",
    "390300756": u"◆NHK「わいわい プログラミング」\nメインコーナー「why!?大喜利」では、月がわりでお題を出すよ！毎月末が応募締め切り。優秀者にはインタビューも。さぁ、キミも投稿してみよう！\nhttp://www.nhk.or.jp/school/programming/oogiri/index.html\n\n◆「キミのびっくりハウスをつくろう！～やねうら部屋 編～」\nキャラクター onnacodomo\n制作 NHK"
}


class WebApiTest(common_testing.BaseTestCase):

    def test_can_download_project_from_project_url(self):
        for project_url, project_id in common_testing.TEST_PROJECT_URL_TO_ID_MAP.iteritems():
            self._set_testresult_folder_subdir(project_id)
            result_folder_path = self._testresult_folder_path
            scratchwebapi.download_project(project_url, result_folder_path)
            if scratch3.is_scratch3_project(result_folder_path):
                scratch3.convert_to_scratch2_data(result_folder_path)

            # TODO: replace with verifying function
            assert scratch.Project(result_folder_path) is not None

    def test_fail_download_project_on_wrong_url(self):
        for wrong_url in ['http://www.tugraz.at', 'http://www.ist.tugraz.at/', 'http://scratch.mit.edu/', 'http://scratch.mit.edu/projects']:
            with self.assertRaises(scratchwebapi.ScratchWebApiError):
                scratchwebapi.download_project(wrong_url, None)
                assert(False & "Exception should prevent getting here, url validation failed")

    def test_can_request_project_code_for_id(self):
        with common.TemporaryDirectory(remove_on_exit=True) as temp_dir:
            for _project_url, project_id in common_testing.TEST_PROJECT_URL_TO_ID_MAP.iteritems():
                scratchwebapi.download_project_code(project_id, temp_dir)
                if scratch3.is_scratch3_project(temp_dir):
                    scratch3.convert_to_scratch2_data(temp_dir)
                project_file_path = os.path.join(temp_dir, scratch._PROJECT_FILE_NAME)
                with open(project_file_path, 'r') as project_code_file:
                    project_code_content = project_code_file.read()
                    raw_project = scratch.RawProject.from_project_code_content(project_code_content)
                    assert raw_project is not None

    def test_can_request_remixes_for_id(self):
        for (project_id, expected_project_remixes) in TEST_PROJECT_ID_TO_REMIXES_MAP.iteritems():
            extracted_project_remixes = scratchwebapi.request_project_remixes_for(project_id)
            assert extracted_project_remixes is not None
            assert isinstance(extracted_project_remixes, list)
            for expected_project_remix in expected_project_remixes:
                assert expected_project_remix in extracted_project_remixes, \
                "'{}' is not in '{}'".format(expected_project_remix, extracted_project_remixes)

    def test_extract_project_details(self):
        details =  scratchwebapi.extract_project_details(10205819, escape_quotes=True)
        assert details.as_dict()["modified_date"] != None
        assert details.as_dict()["shared_date"] != None

    def test_can_request_project_info_for_id(self):
        for (project_id, expected_project_title) in TEST_PROJECT_ID_TO_TITLE_MAP.iteritems():
            title, owner, image_url, instructions, notes_and_credits, stats, history\
                = scratchwebapi.getMetaDataEntry(project_id, 'title', 'username', 'image', 'instructions', 'description', 'stats', 'history')
            assert title == expected_project_title, \
                   "'{}' is not equal to '{}'".format(title, expected_project_title)
            assert owner == TEST_PROJECT_ID_TO_OWNER_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(owner, TEST_PROJECT_ID_TO_OWNER_MAP[project_id])
            assert image_url == TEST_PROJECT_ID_TO_IMAGE_URL_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(image_url, TEST_PROJECT_ID_TO_IMAGE_URL_MAP[project_id])
            assert instructions == TEST_PROJECT_ID_TO_INSTRUCTIONS_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(instructions, TEST_PROJECT_ID_TO_INSTRUCTIONS_MAP[project_id])
            assert notes_and_credits == TEST_PROJECT_ID_TO_NOTES_AND_CREDITS_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(notes_and_credits, TEST_PROJECT_ID_TO_NOTES_AND_CREDITS_MAP[project_id])
            assert isinstance(stats['views'], int)
            assert stats['views'] > 0
            assert isinstance(stats['favorites'], int)
            assert stats['favorites'] >= 0
            assert isinstance(stats['loves'], int)
            assert stats['loves'] >= 0
            assert isinstance(scratchwebapi.convertHistoryDatesToDatetime(history['modified']), datetime)
            assert isinstance(scratchwebapi.convertHistoryDatesToDatetime(history['shared']), datetime)

    def test_can_detect_correct_availability_state_of_project(self):
        project_availability_map = {
            "108628771": False,
            "107178598": False,
            "390300019": True
        }
        for (project_id, expected_availability_state) in project_availability_map.iteritems():
            detected_availability_state = scratchwebapi.request_is_project_available(project_id)
            assert expected_availability_state == detected_availability_state, \
                "State of project #{} is {} but should be {}".format( \
                    project_id, detected_availability_state, expected_availability_state)

    def test_can_detect_correct_visibility_state_of_project(self):
        project_visibility_map = {
            "396543359": scratchwebapi.ScratchProjectVisibiltyState.PRIVATE,
            "387054441": scratchwebapi.ScratchProjectVisibiltyState.PRIVATE,
            "390300019": scratchwebapi.ScratchProjectVisibiltyState.PUBLIC,
            "390299427": scratchwebapi.ScratchProjectVisibiltyState.PUBLIC
        }
        for (project_id, expected_visibility_state) in project_visibility_map.iteritems():
            detected_visibility_state = scratchwebapi.getMetaDataEntry(project_id, 'visibility')
            assert expected_visibility_state == detected_visibility_state

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
