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
#import os
#import subprocess
import unittest

#from scratchtocatrobat import common
#from scratchtocatrobat import test_main

# TODO: fixing Jar build:
#
# class JarTest(test_main.MainTest):
#
#     def __init__(self, *args):
#         super(JarTest, self).__init__(*args)
#
#         def call_jar(args):
#             assert len(args) > 0
#             return subprocess.call(["java", "-cp", converter_jar_path, "-Dpython.security.respectJavaAccessibility=false", "org.python.util.jython", "-jar", converter_jar_path] + args)
#
#         converter_jar_path = os.path.join(common.get_project_base_path(), "dist", "scratch_to_catrobat_converter.jar")
#         assert os.path.isfile(converter_jar_path)
#         self._main_method = call_jar


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
