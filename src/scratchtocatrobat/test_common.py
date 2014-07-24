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
from __future__ import unicode_literals

import os

from scratchtocatrobat import common
from scratchtocatrobat import common_testing


class TestDictAccessWrapper(common.DictAccessWrapper):

    def __init__(self, dict_):
        super(TestDictAccessWrapper, self).__init__(dict_)


class DictAccessWrapperTest(common_testing.BaseTestCase):

    def test_can_use_contains_dynamically_for_keys(self):
        self.assertEqual(False, TestDictAccessWrapper({}).contains_None())
        self.assertEqual(False, TestDictAccessWrapper({'', False, None}).contains_None())
        self.assertEqual(True, TestDictAccessWrapper({'', False, None, 'None'}).contains_None())
        self.assertEqual(True, TestDictAccessWrapper({'keyWithUppercaseAndNumbers123'}).contains_keyWithUppercaseAndNumbers123())
        self.assertEqual(True, TestDictAccessWrapper({u'unicodeKey'}).contains_unicodeKey())

    def test_can_use_index_for_keys(self):
        for dict_access_object in (TestDictAccessWrapper({}), TestDictAccessWrapper({'', False, None})):
            try:
                dict_access_object['not_available_key']
                self.failOnMissingException()
            except KeyError:
                pass
        self.assertEqual(True, TestDictAccessWrapper({'None': True})['None'])
        self.assertEqual(True, TestDictAccessWrapper({'keyWithUppercaseAndNumbers123': True})['keyWithUppercaseAndNumbers123'])
        self.assertEqual(True, TestDictAccessWrapper({u'unicodeKey': True})['unicodeKey'])

    def test_can_use_get_for_keys(self):
        self.assertEqual(None, TestDictAccessWrapper({}).get_None())
        self.assertEqual(None, TestDictAccessWrapper({'', False, None}).get_None())
        self.assertEqual(True, TestDictAccessWrapper({'None': True}).get_None())
        self.assertEqual(True, TestDictAccessWrapper({'keyWithUppercaseAndNumbers123': True}).get_keyWithUppercaseAndNumbers123())
        self.assertEqual(True, TestDictAccessWrapper({u'unicodeKey': True}).get_unicodeKey())


class CommonTest(common_testing.BaseTestCase):

    def test_can_get_audio_file_duration(self):
        test_path_structure_to_file_duration_in_msec_map = {
            ("83a9787d4cb6f3b7632b4ddfebf74367_pop.wav"): 23,
            ("83c36d806dc92327b9e7049a565c6bff_meow.wav"): 847,
        }
        for test_path_structure, expected_duration_in_msec in test_path_structure_to_file_duration_in_msec_map.iteritems():
            audio_file_path = common.get_test_resources_path(*("wav_pcm", test_path_structure))
            assert os.path.exists(audio_file_path)
            assert common.length_of_audio_file_in_msec(audio_file_path) == expected_duration_in_msec
