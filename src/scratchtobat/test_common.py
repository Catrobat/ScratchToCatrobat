from __future__ import unicode_literals

from scratchtobat import common
from scratchtobat import common_testing


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
