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

from scratchtocatrobat.tools import common
from scratchtocatrobat.tools import common_testing
from scratchtocatrobat.scratch import scratch
from scratchtocatrobat.scratch import scratchwebapi
from datetime import datetime

TEST_PROJECT_ID_TO_TITLE_MAP = {
    "10205819": "Dancin' in the Castle",
    "10132588": "Dance back",
    "2365565" : u"Fußball Kapfenstein",
    "117300839": "やねうら部屋（びっくりハウス）"
}

TEST_PROJECT_ID_TO_IMAGE_URL_MAP = {
    "10205819": "https://cdn2.scratch.mit.edu/get_image/project/10205819_144x108.png?v=1368470695.0",
    "10132588": "https://cdn2.scratch.mit.edu/get_image/project/10132588_144x108.png?v=1368129031.0",
    "2365565" : "https://cdn2.scratch.mit.edu/get_image/project/2365565_144x108.png?v=1368072082.0",
    "117300839": "https://cdn2.scratch.mit.edu/get_image/project/117300839_144x108.png?v=1469765618.94"
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
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/10211023_144x108.png',
        'title': "Dancin' in the Castle remake"
    }],
    "10132588"  : [],
    "2365565"   : [],
    "117300839" : [{
        'owner': u'apple502j',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/117443373_144x108.png',
        'title': '\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xef\xbc\x88\xe3\x81\x97\xe3' \
                 '\x81\x99\xe3\x81\x8e\xef\xbc\x89\xe3\x83\x8f\xe3\x82\xa6\xe3\x82\xb9',
        'id': 117443373
    }, {
        'owner': u'nono-san',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/117459825_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117459825
    }, {
        'owner': u'fujiyama',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/117458670_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117458670
    }, {
        'owner': u'nono-san', 'image': 'https://cdn2.scratch.mit.edu/get_image/project/117462865_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix-2',
        'id': 117462865
    }, {
        'owner': u'tomo37564',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/117526717_144x108.png',
        'title': '\xe3\x82\xab\xe3\x82\xaa\xe3\x82\xb9\xe3\x83\xbb\xe3\x82\xaa\xe3\x83\x96\xe3' \
                 '\x83\xbb\xe3\x83\xa4\xe3\x83\x8d\xe3\x82\xa6\xe3\x83\xa9 remix',
        'id': 117526717
    }, {
        'owner': u'MrUdonn',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/117542867_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117542867
    }, {
        'owner': u'nono-san',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/117588399_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix-3',
        'id': 117588399
    }, {
        'owner': u'punpo2007',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/117466753_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117466753
    }, {
        'owner': u'nposss',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/117697631_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b(\xe3' \
                 '\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82\xa6\xe3\x82' \
                 '\xb9) remix \xe3\x81\x8a\xe5\x8c\x96\xe3\x81\x91\xe5\xb1\x8b\xe6\x95\xb7',
        'id': 117697631
    }, {
        'owner': u'haya_tofu',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/117802666_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117802666
    }, {
        'owner': u'Sabomeat',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/117742271_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117742271
    }, {
        'owner': u'kanjitv',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/117805280_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 \xe3\x83\xaa\xe3\x83\x9f\xe3\x83\x83\xe3\x82\xaf' \
                 '\xe3\x82\xb9\xe6\xb8\x88\xe3\x81\xbf',
        'id': 117805280
    }, {
        'owner': u'ikagirl1',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/117820941_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117820941
    }, {
        'owner': u'kenta_suzuki',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/117909085_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 117909085
    }, {
        'owner': u'yuma08',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/118123925_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 118123925
    }, {
        'owner': u'takumigenki',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/118127784_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 118127784
    }, {
        'owner': u'rukiha',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/118556396_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 118556396
    }, {
        'owner': u'tyouhennzinn',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/118505858_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 118505858
    }, {
        'owner': u'naohiro1153',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/118661818_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xb0\xe3\x81\x84\xe3\x80\x82\xe3\x82\x84\xe3\x81\xad\xe3' \
                 '\x81\x86\xe3\x82\x89',
        'id': 118661818
    }, {
        'owner': u'emimi27',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/118772082_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe5\x91\xaa\xe3\x81\x84\xe3\x81\xae\xe3\x83\x8f\xe3\x82\xa6\xe3\x82' \
                 '\xb9\xef\xbc\x89',
        'id': 118772082
    }, {
        'owner': u'mentosu',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/118424749_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 118424749
    }, {
        'owner': u'kenshin007',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/118914295_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 118914295
    }, {
        'owner': u'Ryomap',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/119203970_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 119203970
    }, {
        'owner': u'supertaku',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/119291555_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\xe9\x83\xa8\xe5\xb1\x8b\xef' \
                 '\xbc\x88\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82' \
                 '\xa6\xe3\x82\xb9\xef\xbc\x89 remix',
        'id': 119291555
    }, {
        'owner': u'cheechanGoGo',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/119292702_144x108.png',
        'title': '\xef\xbd\x8d\xe3\x80\x8d',
        'id': 119292702
    }, {
        'owner': u'katakanakana',
        'image': 'https://cdn2.scratch.mit.edu/get_image/project/120985495_144x108.png',
        'title': '\xe3\x82\x84\xe3\x81\xad\xe3\x81\x86\xe3\x82\x89\x08\xe8\xb6\x85\xe8\xb6\x85' \
                 '\xe3\x81\xb3\xe3\x81\xa3\xe3\x81\x8f\xe3\x82\x8a\xe3\x83\x8f\xe3\x82\xa6\xe3' \
                 '\x82\xb9\xef\xbc\x89',
        'id': 120985495
    }]
}

TEST_PROJECT_ID_TO_TAGS_MAP = {
    "10205819": ['animations', 'castle'],
    "10132588": ['music', 'simulations', 'animations'],
    "2365565" : [],
    "117300839": []
}

TEST_PROJECT_ID_TO_INSTRUCTIONS_MAP = {
    "10205819": "Click the flag to run the stack. Click the space bar to change it up!",
    "10132588": "D,4,8 for the animals to move.C,A for background.",
    "2365565" : None,
    "117300839": "◆「Why!?大喜利」8月のお題 ・キミのびっくりハウスをつくろう！～やねうら部屋 編～ " \
                 "広い“屋根裏部屋”には、何もないみたいだね。好きなものを書いたり、おいたりして“びっく" \
                 "り”を作ろう。スプライトには助っ人として、マックスとリンゴがあるぞ！ ◆自由にリミックス" \
                 "（改造）して、遊んでください！ 面白い作品ができたら、こちらまで投稿を！ http://www.nhk." \
                 "or.jp/xxx ※リミックス作品を投稿する時は”共有”を忘れないでね。"
}

TEST_PROJECT_ID_TO_NOTES_AND_CREDITS_MAP = {
    "10205819": "First project on Scratch! This was great.",
    "10132588": "",
    "2365565" : "None",
    "117300839": "◆NHK「わいわい プログラミング」 メインコーナー「why!?大喜利」では、月がわりでお題を出す" \
                 "よ！毎月末が応募締め切り。優秀者にはインタビューも。さぁ、キミも投稿してみよう！ " \
                 "http://www.nhk.or.jp/school/programming/oogiri/index.html ◆「キミのびっくりハウ" \
                 "スをつくろう！～やねうら部屋 編～」 キャラクター onnacodomo 制作 NHK"
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

    def test_can_request_project_image_url_for_id(self):
        for (project_id, expected_project_image_URL) in TEST_PROJECT_ID_TO_IMAGE_URL_MAP.iteritems():
            extracted_project_image_URL = scratchwebapi.request_project_image_url_for(project_id)
            assert extracted_project_image_URL is not None
            assert extracted_project_image_URL == expected_project_image_URL, \
                   "'{}' is not equal to '{}'".format(extracted_project_image_URL, expected_project_image_URL)

    def test_can_request_project_owner_for_id(self):
        for (project_id, expected_project_owner) in TEST_PROJECT_ID_TO_OWNER_MAP.iteritems():
            extracted_project_owner = scratchwebapi.request_project_owner_for(project_id)
            assert extracted_project_owner is not None
            assert extracted_project_owner == expected_project_owner, \
                   "'{}' is not equal to '{}'".format(extracted_project_owner, expected_project_owner)

    def test_can_request_project_instructions_for_id(self):
        for (project_id, expected_project_instructions) in TEST_PROJECT_ID_TO_INSTRUCTIONS_MAP.iteritems():
            extracted_project_instructions = scratchwebapi.request_project_instructions_for(project_id)
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
                   "'{}' is not equal to '{}'".format(extracted_project_remixes,
                                                      expected_project_remixes)

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
            assert extracted_project_info.image_url is not None
            assert extracted_project_info.image_url == TEST_PROJECT_ID_TO_IMAGE_URL_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(extracted_project_info.image_url, TEST_PROJECT_ID_TO_IMAGE_URL_MAP[project_id])
            assert extracted_project_info.instructions == TEST_PROJECT_ID_TO_INSTRUCTIONS_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(extracted_project_info.instructions, TEST_PROJECT_ID_TO_INSTRUCTIONS_MAP[project_id])
            assert extracted_project_info.notes_and_credits == TEST_PROJECT_ID_TO_NOTES_AND_CREDITS_MAP[project_id], \
                   "'{}' is not equal to '{}'".format(extracted_project_info.notes_and_credits, TEST_PROJECT_ID_TO_NOTES_AND_CREDITS_MAP[project_id])
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
            assert isinstance(extracted_project_info.modified_date, datetime)
            assert extracted_project_info.shared_date is not None
            assert isinstance(extracted_project_info.shared_date, datetime)

    def test_can_detect_correct_availability_state_of_project(self):
        project_availability_map = {
            "108628771": False,
            "107178598": True,
            "95106124": True
        }
        for (project_id, expected_availability_state) in project_availability_map.iteritems():
            detected_availability_state = scratchwebapi.request_is_project_available(project_id)
            assert expected_availability_state == detected_availability_state

    def test_can_detect_correct_visibility_state_of_project(self):
        project_visibility_map = {
            "107178598": scratchwebapi.ScratchProjectVisibiltyState.PRIVATE,
            "95106124": scratchwebapi.ScratchProjectVisibiltyState.PUBLIC,
            "85594786": scratchwebapi.ScratchProjectVisibiltyState.PUBLIC
        }
        for (project_id, expected_visibility_state) in project_visibility_map.iteritems():
            detected_visibility_state = scratchwebapi.request_project_visibility_state_for(project_id)
            assert expected_visibility_state == detected_visibility_state

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
