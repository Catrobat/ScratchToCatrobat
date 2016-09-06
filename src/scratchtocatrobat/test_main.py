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
#import subprocess
import unittest

from scratchtocatrobat.tools import common
from scratchtocatrobat.tools import common_testing
from scratchtocatrobat.converter import converter
from scratchtocatrobat import main
from scratchtocatrobat.scratch import scratchwebapi
from scratchtocatrobat.tools import helpers

_DEFAULT_INTERPRETER = common.JYTHON_BINARY


class MainTest(common_testing.ProjectTestCase):

    def __init__(self, *args):
        super(MainTest, self).__init__(*args)
        self._main_method = main.run_converter
        self.base_exec_args = ["python", os.path.join(common.get_project_base_path(), "run")]

    def execute_run_script(self, args, env=None):
        if not env:
            env = dict()
            assert os.environ.get('JYTHON_HOME')
            env['JYTHON_HOME'] = helpers.config.get("PATHS", "jython_home")
            env = os.environ
        exec_args = self.base_exec_args + list(args)
        #return common_testing.call_returning_exit(exec_args, env=env)
        return common_testing.call_returning_exit_and_output(exec_args, env=env)[0]

    def execute_main_module_check(self, module_args=None, interpreter=None, interpreter_options=None):
        if interpreter is None:
            assert 'JYTHON_HOME' in self.test_environ, "Environment variable JYTHON_HOME must be set!"
            interpreter = self.test_environ['JYTHON_HOME'] + "/bin/" + _DEFAULT_INTERPRETER
        if not module_args:
            module_args = ["--version"]
        if not interpreter_options:
            interpreter_options = []
        assert isinstance(module_args, (list, tuple))
        assert isinstance(interpreter_options, (list, tuple))
        assert self.test_environ

        call_args = [interpreter] + interpreter_options + ["-m", main.__name__] + module_args
        return_val, (stdout, stderr) = common_testing.call_returning_exit_and_output(call_args, env=self.test_environ)
        return return_val, (stdout, stderr)

    def setUp(self):
        super(MainTest, self).setUp()
        self.test_environ = dict(os.environ)

    def assertMainSuccess(self, args, project_id):
        output_path = self._testresult_folder_path
        if len(args) == 1:
            args += [output_path]
        return_val = self.execute_run_script(args)
        assert return_val == helpers.ExitCode.SUCCESS

        project_name = scratchwebapi.request_project_title_for(project_id)
        self.assertValidCatrobatProgramPackageAndUnpackIf(converter.ConvertedProject._converted_output_path(output_path, project_name), project_name)

    def test_can_provide_catrobat_program_for_scratch_project_link(self):
        for project_url, project_id in common_testing.TEST_PROJECT_URL_TO_ID_MAP.iteritems():
            self.assertMainSuccess([project_url], project_id)

    def test_can_provide_catrobat_program_for_scratch_project_file(self):
        for project_filename, project_id in common_testing.TEST_PROJECT_FILENAME_TO_ID_MAP.iteritems():
            self.assertMainSuccess([common_testing.get_test_project_packed_file(project_filename)], project_id)

# FIXME: needs an regular python installation with the same module dependencies (docopt)
#     def test_fail_on_execution_with_non_jython(self):
#         package_subdir_path = os.path.join(*main.__name__.split(".")[:-1])
#         base_package_path = os.path.dirname(main.__file__).replace(package_subdir_path, "")
#         self.test_environ["PYTHONPATH"] += os.pathsep + base_package_path
#
#         return_val, (stdout, stderr) = self.execute_main_module_check(module_args=["--check-env-only"], interpreter="python")
#
#         assert stderr, stdout
#         assert "Jython" in stderr
#         assert return_val == main.EXIT_FAILURE

    def test_fail_on_expected_jython_java_access_property_missing(self):
        #package_subdir_path = os.path.join(*main.__name__.split(".")[:-1])
        #base_package_path = os.path.dirname(main.__file__).replace(package_subdir_path, "")
        #self.test_environ["PYTHONPATH"] += os.pathsep + base_package_path

        return_val, (stdout, stderr) = self.execute_main_module_check(interpreter_options=["-D%s=true" % helpers.JYTHON_RESPECT_JAVA_ACCESSIBILITY_PROPERTY])
        assert stderr, stdout
        assert "Jython registry property 'python.security.respectJavaAccessibility' must be set to 'false'" in stderr
        assert return_val == helpers.ExitCode.FAILURE

    def test_check_if_sox_binary_can_be_found(self):
        return_val, (stdout, stderr) = self.execute_main_module_check()
        assert stderr, stdout
        assert "Sox binary must be available on system path" not in stderr
        assert return_val == helpers.ExitCode.SUCCESS

    def test_can_get_catrobat_language_version(self):
        return_val, (stdout, _) = self.execute_main_module_check()
        assert "Catrobat language version:" in stdout
        # NOTE: with Jython the docopt module prints some debug information as first stderr line
        # assert not stderr
        assert return_val == helpers.ExitCode.SUCCESS

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
