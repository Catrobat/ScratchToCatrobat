import os
import subprocess
import unittest

from scratchtobat import common
from scratchtobat import test_main


class JarTest(test_main.MainTest):

    def __init__(self, *args):
        super(JarTest, self).__init__(*args)

        def call_jar(args):
            assert len(args) > 0
            return subprocess.call(["java", "-cp", converter_jar_path, "-Dpython.security.respectJavaAccessibility=false", "org.python.util.jython", "-jar", converter_jar_path] + args)

        converter_jar_path = os.path.join(common.get_project_base_path(), "dist", "scratch_to_catrobat_converter.jar")
        assert os.path.isfile(converter_jar_path)
        self._main_method = call_jar


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
