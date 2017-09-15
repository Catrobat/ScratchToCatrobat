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

import os
import unittest

from scratchtocatrobat.tools import common
from scratchtocatrobat.tools import common_testing


class TestDictAccessWrapper(common.DictAccessWrapper):

    def __init__(self, dict_):
        super(TestDictAccessWrapper, self).__init__(dict_)


class DictAccessWrapperTest(common_testing.BaseTestCase):

    def test_can_use_contains_dynamically_for_keys(self):
        assert not TestDictAccessWrapper({}).contains_None()
        assert not TestDictAccessWrapper({'', False, None}).contains_None()
        assert TestDictAccessWrapper({'', False, None, 'None'}).contains_None()
        assert TestDictAccessWrapper({'keyWithUppercaseAndNumbers123'}).contains_keyWithUppercaseAndNumbers123()
        assert TestDictAccessWrapper({u'unicodeKey'}).contains_unicodeKey()

    def test_can_use_index_for_keys(self):
        for dict_access_object in (TestDictAccessWrapper({}), TestDictAccessWrapper({'', False, None})):
            try:
                dict_access_object['not_available_key']
                self.failOnMissingException()
            except KeyError:
                pass
        assert TestDictAccessWrapper({'None': True})['None']
        assert TestDictAccessWrapper({'keyWithUppercaseAndNumbers123': True})['keyWithUppercaseAndNumbers123']
        assert TestDictAccessWrapper({u'unicodeKey': True})['unicodeKey']

    def test_can_use_get_for_keys(self):
        assert TestDictAccessWrapper({}).get_None() is None
        assert TestDictAccessWrapper({'', False, None}).get_None() is None
        assert TestDictAccessWrapper({'None': True}).get_None()
        assert TestDictAccessWrapper({'keyWithUppercaseAndNumbers123': True}).get_keyWithUppercaseAndNumbers123()
        assert TestDictAccessWrapper({u'unicodeKey': True}).get_unicodeKey()

    def test_can_not_modify_wrapper_dict_content(self):
        test_dict = dict((x, "unchanged" + str(x)) for x in range(5))
        dict_wrapper = TestDictAccessWrapper(test_dict)
        test_key = 1
        value_before_dict_change = dict_wrapper[test_key]
        test_dict[test_key] = "changed"
        assert value_before_dict_change == dict_wrapper[test_key]


class CommonTest(common_testing.BaseTestCase):

    def test_can_get_audio_file_duration(self):
        test_path_structure_to_file_duration_in_msec_map = {
            ("83a9787d4cb6f3b7632b4ddfebf74367_pop.wav"): 23,
            ("83c36d806dc92327b9e7049a565c6bff_meow.wav"): 847,
        }
        for test_path_structure, expected_duration_in_msec in test_path_structure_to_file_duration_in_msec_map.iteritems():
            audio_file_path = common_testing.get_test_resources_path(*("wav_pcm", test_path_structure))
            assert os.path.exists(audio_file_path)
            self.assertAlmostEqual(common.length_of_audio_file_in_secs(audio_file_path), expected_duration_in_msec / 1000.0, delta=0.001)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
