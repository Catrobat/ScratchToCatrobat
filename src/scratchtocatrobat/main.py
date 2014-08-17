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
import logging
import os
import shutil
import sys
from docopt import docopt
from java.io import IOError
from java.lang import System

from scratchtocatrobat import common
from scratchtocatrobat import converter
from scratchtocatrobat import scratch
from scratchtocatrobat import scratchwebapi

log = logging.getLogger(__name__)

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def run_converter(arguments):
    log.info("Called with args: '{}'".format(arguments))

    def check_environment_settings():
        if "java" not in sys.platform:
            common.ScratchtobatError("Must be called with Jython interpreter. Aborting.")
        if System.getProperty("python.security.respectJavaAccessibility") != 'false':
            common.ScratchtobatError("Jython registry property 'python.security.respectJavaAccessibility' must be set to 'false'. Aborting.")

    check_environment_settings()

    scratch_project_file_or_url, output_dir, extract_resulting_catrobat = arguments["<project-url-or-package-path>"], arguments["<output-dir>"], arguments["--extracted"]
    temp_rm = not arguments["--no-temp-rm"]
    try:
        if not os.path.isdir(output_dir):
            raise EnvironmentError("Output folder must be a directory, but is %s" % output_dir)
        with common.TemporaryDirectory(remove_on_exit=temp_rm) as scratch_project_dir:
            if scratch_project_file_or_url.startswith("http://"):
                log.info("Downloading project from URL: '{}' to temp dir {} ...".format(scratch_project_file_or_url, scratch_project_dir))
                scratchwebapi.download_project(scratch_project_file_or_url, scratch_project_dir)
            elif os.path.isfile(scratch_project_file_or_url):
                log.info("Extracting project from path: '{}' ...".format(scratch_project_file_or_url))
                common.extract(scratch_project_file_or_url, scratch_project_dir)
            else:
                log.info("Loading project from path: '{}' ...".format(scratch_project_file_or_url))
                scratch_project_dir = scratch_project_file_or_url
            project = scratch.Project(scratch_project_dir)
            log.info("Converting scratch project '%s' into output folder: %s", project.name, output_dir)
            catrobat_program_path = converter.save_as_catrobat_program_package_to(project, output_dir)
            if extract_resulting_catrobat:
                extraction_path = os.path.join(output_dir, os.path.splitext(os.path.basename(catrobat_program_path))[0])
                if os.path.exists(extraction_path):
                    shutil.rmtree(extraction_path)
                common.makedirs(extraction_path)
                common.extract(catrobat_program_path, extraction_path)
    except (common.ScratchtobatError, EnvironmentError, IOError) as e:
        log.exception(e)
        return EXIT_FAILURE
    except Exception, e:
        log.exception(e)
        return EXIT_FAILURE
    return EXIT_SUCCESS

if __name__ == '__main__':
    log = logging.getLogger("scratchtocatrobat.main")
    usage = '''ScratchToCatrobat converter

    Usage:
      'main.py' <project-url-or-package-path> <output-dir> [--extracted] [--no-temp-rm]

    Options:
      -h --help     Show this screen.
      -e --extracted    Extract resulting Catrobat program in output-dir.
    '''
    arguments = docopt(usage)
    sys.exit(run_converter(arguments))
