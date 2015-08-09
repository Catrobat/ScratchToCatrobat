#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2015 The Catrobat Team
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

import os
import sys

################################################################################
# IMMUTABLE PATHS
################################################################################
HELPER_PATH = os.path.realpath(os.path.dirname(__file__))
APP_PATH = os.path.join(HELPER_PATH, "..", "..", "..")
SRC_PATH = os.path.join(APP_PATH, "src")
LIB_PATH = os.path.join(APP_PATH, "lib")
CFG_DEFAULT_FILE_NAME = "default.ini"
CFG_CUSTOM_ENV_FILE_NAME = "environment.ini"
CFG_PATH = os.path.join(APP_PATH, "config")


################################################################################
# HELPERS
################################################################################
class CatrobatConfigParser(object):
    def __init__(self):
        import ConfigParser
        self.config_parser = ConfigParser.ConfigParser()
    def get(self, section, option):
        import re
        entry = self.config_parser.get(section, option)
        entry = entry.replace("${APP_PATH}", APP_PATH)
        entry = entry.replace("${LIB_PATH}", LIB_PATH)
        entry = entry.replace("${SRC_PATH}", SRC_PATH)
        entry = entry.replace("${CFG_PATH}", CFG_PATH)
        regex = re.compile(r'\$\{([^\}]*)\}')
        if len(regex.findall(entry)) > 0:
            error("Unexpected placeholder token found in helpers file (section: %s, option: %s)!" % (section, option))
        return entry
    def read(self, filenames):
        return self.config_parser.read(filenames)

class ExitCode(object):
    SUCCESS = 0
    FAILURE = 1

def error(msg):
    print("ERROR: {0}".format(msg))
    sys.exit(ExitCode.FAILURE)

def make_dir_if_not_exists(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        elif not os.path.isdir(path):
            error("Invalid path '{0}'. This is NO directory.".format(path))
    except Exception, e:
        error(e)

def application_info(key):
    return config.get("APPLICATION", key)

def catrobat_info(key):
    return config.get("CATROBAT", key)

def scratch_info(key):
    return config.get("SCRATCH", key)

def _setup_configuration():
    make_dir_if_not_exists(CFG_PATH)
    config_default_file_path = os.path.join(CFG_PATH, CFG_DEFAULT_FILE_NAME)
    config_custom_env_file_path = os.path.join(CFG_PATH, CFG_CUSTOM_ENV_FILE_NAME)

    if not os.path.exists(config_default_file_path):
        error("No such file '%s' exists." % CFG_DEFAULT_FILE_NAME)
    if os.path.isdir(config_default_file_path):
        error("Config file '%s' should be file, but is a directory!" % CFG_DEFAULT_FILE_NAME)
    if not os.access(config_default_file_path, os.R_OK):
        error("No file permissions to read helpers file '%s'!" % CFG_DEFAULT_FILE_NAME)

    config = CatrobatConfigParser()
    if os.path.exists(config_custom_env_file_path):
        if os.path.isdir(config_custom_env_file_path):
            error("Config file '%s' should be file, but is a directory!" % CFG_CUSTOM_ENV_FILE_NAME)
        if not os.access(config_custom_env_file_path, os.R_OK):
            error("No file permissions to read helpers file '%s'!" % CFG_CUSTOM_ENV_FILE_NAME)
        config.read(config_custom_env_file_path)
    else:
        config.read(config_default_file_path)
    return config

config = _setup_configuration()

JYTHON_RESPECT_JAVA_ACCESSIBILITY_PROPERTY = "python.security.respectJavaAccessibility"
