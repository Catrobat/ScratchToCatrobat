import os
import unittest

TEST_PROJECT_URLS = ['http://scratch.mit.edu/projects/10205819/'] 


def get_test_resources_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test/res"))


def get_test_project_path(project_name):
    return os.path.join(get_test_resources_path(), "sb2", project_name)


class ScratchtobatTestCase(unittest.TestCase):
    
    def assertScriptClasses(self, expected_script_class, expected_brick_classes, script):
        self.assertEqual(expected_script_class, [script.__class__], "Script class is not matching")
        bricks = script.getBrickList()
        self.assertTrue(bricks, "No bricks.")
        self.assertEqual(len(expected_brick_classes), len(bricks), "Wrong number of bricks.")
        self.assertEqual(expected_brick_classes, [_.__class__ for _ in bricks], "Wrong brick classes.")