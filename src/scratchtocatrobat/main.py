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
from __future__ import print_function

import logging
import os
import shutil
import sys
from docopt import docopt

from scratchtocatrobat import logger

logger.initialize_logging()
log = logging.getLogger(__name__)

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
_JYTHON_RESPECT_JAVA_ACCESSIBILITY_PROPERTY = "python.security.respectJavaAccessibility"


def run_converter(scratch_project_file_or_url, output_dir, extract_resulting_catrobat=False, temp_rm=True, show_version_only=False):
    # import pudb; pu.db

    def check_base_environment():
        if "java" not in sys.platform:
            raise EnvironmentError("Must be called with Jython interpreter.")
        if System.getProperty(_JYTHON_RESPECT_JAVA_ACCESSIBILITY_PROPERTY) != 'false':
            raise EnvironmentError("Jython registry property '%s' must be set to 'false'." % _JYTHON_RESPECT_JAVA_ACCESSIBILITY_PROPERTY)

    def check_converter_environment():
        # TODO: refactor to combined class with explicit environment check method
        tools.svgtopng._checked_batik_jar_path()
        tools.wavconverter._checked_sox_path()

    try:
        from java.io import IOError
        from java.lang import System
    except ImportError:
        log.error("Must be called with Jython interpreter.")
        return EXIT_FAILURE

    # nested import to be able to check for Jython interpreter first
    from scratchtocatrobat import catrobat
    from scratchtocatrobat import common
    from scratchtocatrobat import converter
    from scratchtocatrobat import scratch
    from scratchtocatrobat import scratchwebapi
    from scratchtocatrobat import tools

    try:
        check_base_environment()
        check_converter_environment()

        import org.catrobat.catroid.common as catcommon
        if show_version_only:
            # TODO: should return last modfication date or source control tag of Catrobat classes
            print("Catrobat language version:", catrobat.CATROBAT_LANGUAGE_VERSION)
        else:
            log.info("calling converter")
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
                converted_project = converter.converted(project)
                catrobat_program_path = converted_project.save_as_catrobat_package_to(output_dir)
                if extract_resulting_catrobat:
                    extraction_path = os.path.join(output_dir, os.path.splitext(os.path.basename(catrobat_program_path))[0])
                    if os.path.exists(extraction_path):
                        shutil.rmtree(extraction_path)
                    common.makedirs(extraction_path)
                    common.extract(catrobat_program_path, extraction_path)
    except (common.ScratchtobatError, EnvironmentError, IOError) as e:
        log.error(e)
        return EXIT_FAILURE
    except Exception as e:
        log.exception(e)
        return EXIT_FAILURE
    return EXIT_SUCCESS

if __name__ == '__main__':
    log = logging.getLogger("scratchtocatrobat.main")
    usage = '''Scratch to Catrobat converter

    Usage:
      'main.py' <project-url-or-package-path> <output-dir> [--extracted] [--no-temp-rm]
      'main.py' --version

    Options:
      -h --help         Show this screen.
      --version         Show version.
      -e --extracted    Extract resulting Catrobat program in output-dir.
    '''
    arguments = docopt(usage)
    try:
        kwargs = {}
        kwargs['extract_resulting_catrobat'] = arguments["--extracted"]
        kwargs['temp_rm'] = not arguments["--no-temp-rm"]
        kwargs['show_version_only'] = arguments["--version"]
        sys.exit(run_converter(arguments["<project-url-or-package-path>"], arguments["<output-dir>"], **kwargs))
    except Exception as e:
        log.exception(e)
        sys.exit(EXIT_FAILURE)

