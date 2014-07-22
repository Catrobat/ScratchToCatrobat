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
import sys
from java.io import IOError
from java.lang import System

from scratchtocatrobat import converter
from scratchtocatrobat import common
from scratchtocatrobat import scratch
from scratchtocatrobat import scratchwebapi

log = logging.getLogger(__name__)

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def scratchtobat_main(argv):
    log.info("Called with args: '{}'".format(argv))

    def usage():
        print "usage: jython main.py <scratch-file or project url to be converted> <output_dir>"
        print "Example 1: jython main.py http://scratch.mit.edu/projects/10205819/ output"
        print "Example 2: jython main.py dancing_castle.scratch output"
        sys.exit(EXIT_FAILURE)

    def check_environment_settings():
        if "java" not in sys.platform:
            common.ScratchtobatError("Must be called with Jython interpreter. Aborting.")
        if System.getProperty("python.security.respectJavaAccessibility") != 'false':
            common.ScratchtobatError("Jython registry property 'python.security.respectJavaAccessibility' must be set to 'false'. Aborting.")

    check_environment_settings()

    if len(argv) != 2:
        usage()

    scratch_project_file_or_url, output_dir = argv
    try:
        if not os.path.isdir(output_dir):
            raise EnvironmentError("Output folder must be a directory, but is %s" % output_dir)
        with common.TemporaryDirectory() as scratch_project_dir:
            if scratch_project_file_or_url.startswith("http://"):
                log.info("Downloading project from URL: '{}' ...".format(scratch_project_file_or_url))
                scratchwebapi.download_project(scratch_project_file_or_url, scratch_project_dir)
            else:
                log.info("Extracting project from path: '{}' ...".format(scratch_project_file_or_url))
                scratch.extract_project(scratch_project_file_or_url, scratch_project_dir)
            scratch_project = scratch.Project(scratch_project_dir)
            log.info("Converting scratch project %s into output folder: %s", scratch_project, output_dir)
            converter.save_as_catrobat_program_package_to(scratch_project, output_dir)
    except (common.ScratchtobatError, EnvironmentError, IOError) as e:
        log.error(e)
        return EXIT_FAILURE
    return EXIT_SUCCESS

if __name__ == '__main__':
    log = logging.getLogger("scratchtocatrobat.main")
    sys.exit(scratchtobat_main(sys.argv[1:]))
