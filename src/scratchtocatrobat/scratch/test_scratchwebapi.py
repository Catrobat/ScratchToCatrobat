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
    "10205819": "Dancin' in the Castle",
    "10132588": "Dance back",
    "2365565" : u"Fußball Kapfenstein",
    "117300839": u"やねうら部屋（びっくりハウス）"
}

TEST_PROJECT_ID_TO_IMAGE_URL_MAP = {
    "10205819": "https://cdn2.scratch.mit.edu/get_image/project/10205819_480x360.png",
    "10132588": "https://cdn2.scratch.mit.edu/get_image/project/10132588_480x360.png",
    "2365565" : "https://cdn2.scratch.mit.edu/get_image/project/2365565_480x360.png",
    "117300839": "https://cdn2.scratch.mit.edu/get_image/project/117300839_480x360.png"
}

TEST_PROJECT_ID_TO_OWNER_MAP = {
    "10205819": "jschombs",
    "10132588": "psush09",
    "2365565" : "hej_wickie_hej",
    "117300839": "NHK_for_School"
}

TEST_PROJECT_ID_TO_REMIXES_MAP = {
    "10205819"  : [{
        'id'   : 10211023,
        'owner': 'Amanda69',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/10211023.png',
        'title': "Dancin' in the Castle remake"
    }],
    "10132588"  : [],
    "2365565"   : [],
    "117300839" : [{
        'owner': u'apple502j',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117443373.png',
        'title': '\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xef\xbc\x88\xe3\x81\x97\xe3' \
                 '\x81\x99\xe3\x81\x8e\xef\xbc\x89\xe3\x83\x8f\xe3\x82\xa6\xe3\x82\xb9',
        'id': 117443373
    }, {
        'owner': u'nono-san',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117459825.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117459825
    }, {
        'owner': u'fujiyama',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117458670.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117458670
    }, {
        'owner': u'nono-san', 'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117462865.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix-2',
        'id': 117462865
    }, {
        'owner': u'tomo37564',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117526717.png',
        'title': '\xe3\x82\xab\xe3\x82\xaa\xe3\x82\xb9\xe3\x83\xbb\xe3\x82\xaa\xe3\x83\x96\xe3' \
                 '\x83\xbb\xe3\x83\xa4\xe3\x83\x8d\xe3\x82\xa6\xe3\x83\xa9 remix',
        'id': 117526717
    }, {
        'owner': u'MrUdonn',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117542867.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117542867
    }, {
        'owner': u'nono-san',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117588399.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix-3',
        'id': 117588399
    }, {
        'owner': u'punpo2007',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117466753.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117466753
    }, {
        'owner': u'nposss',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117697631.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b(\xe3' \
                 '\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82\xa6\xe3\x82' \
                 '\xb9) remix \xe3\x81\x8a\xe5\x8c\x96\xe3\x81\x91\xe5\xb1\x8b\xe6\x95\xb7',
        'id': 117697631
    }, {
        'owner': u'haya_tofu',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117802666.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117802666
    }, {
        'owner': u'Sabomeat',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117742271.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117742271
    }, {
        'owner': u'kanjitv',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117805280.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 \xe3\x83\xaa\xe3\x83\x9f\xe3\x83\x83\xe3\x82\xaf' \
                 '\xe3\x82\xb9\xe6\xb8\x88\xe3\x81\xbf',
        'id': 117805280
    }, {
        'owner': u'ikagirl1',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117820941.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117820941
    }, {
        'owner': u'kenta_suzuki',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/117909085.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117909085
    }, {
        'owner': u'yuma08',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/118123925.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 118123925
    }, {
        'owner': u'takumigenki',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/118127784.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 118127784
    }, {
        'owner': u'rukiha',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/118556396.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 118556396
    }, {
        'owner': u'tyouhennzinn',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/118505858.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 118505858
    }, {
        'owner': u'naohiro1153',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/118661818.png',
        'title': '\xe3\x82\x84\xe3\x81\xb0\xe3\x81\x84\xe3\x80\x82\xe3\x82\x84\xe3\x81\xad\xe3' \
                 '\x81\x86\xe3\x82\x89',
        'id': 118661818
    }, {
        'owner': u'emimi27',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/118772082.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe5\x91\xaa\xe3\x81\x84\xe3\x81\xae\xe3\x83\x8f\xe3\x82\xa6\xe3\x82' \
                 '\xb9\xef\xbc\x89',
        'id': 118772082
    }, {
        'owner': u'mentosu',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/118424749.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 118424749
    }, {
        'owner': u'kenshin007',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/118914295.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 118914295
    }, {
        'owner': u'Ryomap',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/119203970.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 119203970
    }, {
        'owner': u'supertaku',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/119291555.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 119291555
    }, {
        'owner': u'cheechanGoGo',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/119292702.png',
        'title': '\xef\xbd\x8d\xe3\x80\x8d',
        'id': 119292702
    }, {
        'owner': u'katakanakana',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/120985495.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\x08\xe8\xb6\x85\xe8\xb6\x85' \
                 '\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82\xa6\xe3' \
                 '\x82\xb9\xef\xbc\x89',
        'id': 120985495
    }, {
        'owner': u'Lily-co',
        'image': 'https://uploads.scratch.mit.edu/projects/thumbnails/125370675.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 125370675
    }]
}

TEST_PROJECT_ID_TO_INSTRUCTIONS_MAP = {
    "10205819": "Click the flag to run the stack. Click the space bar to change it up!",
    "10132588": "D,4,8 for the animals to move.C,A for background. ",
    "2365565" : "",
    "117300839": u"◆「Why!?大喜利」8月のお題\n・キミのびっくりハウスをつくろう！～やねうら部屋 編～\n\n" \
                 u"広い“屋根裏部屋”には、何もないみたいだね。好きなものを書いたり、おいたりして“びっく" \
                 u"り”を作ろう。スプライトには助っ人として、マックスとリンゴがあるぞ！\n\n" \
                 u"◆自由にリミックス（改造）して、遊んでください！\n面白い作品ができたら、こちらまで投稿を！\nhttp://www.nhk." \
                 u"or.jp/xxx\n※リミックス作品を投稿する時は”共有”を忘れないでね。\n"
}

TEST_PROJECT_ID_TO_NOTES_AND_CREDITS_MAP = {
    "10205819": "First project on Scratch! This was great.",
    "10132588": "",
    "2365565" : "",
    "117300839": u"◆NHK「わいわい プログラミング」\nメインコーナー「why!?大喜利」では、月がわりでお題を出すよ！毎月末が応募締め切り。優秀者にはインタビューも。さぁ、キミも投稿してみよう！\nhttp://www.nhk.or.jp/school/programming/oogiri/index.html\n\n◆「キミのびっくりハウスをつくろう！～やねうら部屋 編～」\nキャラクター onnacodomo\n制作 NHK\n"
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
            extracted_project_remixes = extracted_project_remixes[:len(expected_project_remixes)]
            assert extracted_project_remixes == expected_project_remixes, \
                "'{}' is not equal to '{}'".format(extracted_project_remixes,
                                                   expected_project_remixes)
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
            "95106124": True
        }
        for (project_id, expected_availability_state) in project_availability_map.iteritems():
            detected_availability_state = scratchwebapi.request_is_project_available(project_id)
            assert expected_availability_state == detected_availability_state, \
                "State of project #{} is {} but should be {}".format( \
                    project_id, detected_availability_state, expected_availability_state)

    def test_can_detect_correct_visibility_state_of_project(self):
        project_visibility_map = {
            "107178598": scratchwebapi.ScratchProjectVisibiltyState.PRIVATE,
            "123242912": scratchwebapi.ScratchProjectVisibiltyState.PRIVATE,
            "95106124": scratchwebapi.ScratchProjectVisibiltyState.PUBLIC,
            "85594786": scratchwebapi.ScratchProjectVisibiltyState.PUBLIC
        }
        for (project_id, expected_visibility_state) in project_visibility_map.iteritems():
            detected_visibility_state = scratchwebapi.getMetaDataEntry(project_id, 'visibility')
            assert expected_visibility_state == detected_visibility_state

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
