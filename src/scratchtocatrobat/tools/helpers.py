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

from __future__ import print_function
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
class cli_colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[1;32m'
    WARNING = '\033[93m'
    FAIL = '\033[0;31;5m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class CatrobatConfigParser(object):
    def __init__(self):
        import ConfigParser
        self.config_parser = ConfigParser.ConfigParser()
    def _populate_placeholders_of_entry(self, entry, section, option):
        import re
        entry = entry.replace("${APP_PATH}", APP_PATH)
        entry = entry.replace("${LIB_PATH}", LIB_PATH)
        entry = entry.replace("${SRC_PATH}", SRC_PATH)
        entry = entry.replace("${CFG_PATH}", CFG_PATH)
        regex = re.compile(r'\$\{([^\}]*)\}')
        if len(regex.findall(entry)) > 0:
            error("Unexpected placeholder token found in helpers file (section: %s, option: %s)!" % (section, option))
        return entry
    def items(self, section):
        entries = self.config_parser.items(section)
        return [(option, self._populate_placeholders_of_entry(entry, section, option)) for (option, entry) in entries]
    def get(self, section, option):
        entry = self.config_parser.get(section, option)
        return self._populate_placeholders_of_entry(entry, section, option)
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

def tag_name_of_used_catroid_hierarchy():
    return config.get("CATROID", "tag_name_of_used_hierarchy")

def latest_catroid_repository_release_data():
    import urllib2, json, time
    cached_file_path = os.path.join(config.get("PATHS", "tmp"), "cache_catroid_latest_release.dat")
    url = config.get("CATROID", "repository_api_show_tags_url")
    try:
        # check if cached file exists
        if os.path.isfile(cached_file_path):
            with open(cached_file_path, "r") as infile:
                json_data = infile.read().replace('\n', '')
            one_hour_ago = time.time() - 60*60 
            st = os.stat(cached_file_path)
            ctime = st.st_ctime
            if ctime < one_hour_ago:
                os.remove(cached_file_path)

        # check if cached file still (!) exists
        if not os.path.isfile(cached_file_path):
            print("        ------->>>>>> NEW REQUEST <<<<<<<<<<<----------")
            response = urllib2.urlopen(url);
            json_data = response.read()

        latest_release_data = json.loads(json_data)
        with open(cached_file_path, 'w') as outfile:
            outfile.write(json_data)
        return latest_release_data
    except Exception:
        return None

def print_info_or_version_screen(show_version_only, catrobat_language_version):
    tag_name = tag_name_of_used_catroid_hierarchy()
    latest_release_data = latest_catroid_repository_release_data()
    if not show_version_only:
        print("-"*80)
        print(application_info("name"))
        print("-"*80)
    print(application_info("short_name"), "Version:", application_info("version"))
    print("Catrobat language version:", catrobat_language_version)
    print("Catroid version of currently used hierarchy:", tag_name)
    if latest_release_data:
        print("Latest Catroid release: %s (%s)" % (latest_release_data["tag_name"], latest_release_data["published_at"]))
        if tag_name != latest_release_data["tag_name"]:
            print("%sA NEW CATROID RELEASE IS AVAILABLE!\nPLEASE UPDATE THE CLASS HIERARCHY OF THE CONVERTER FROM CATROID VERSION %s TO VERSION %s%s" % (cli_colors.FAIL, tag_name, latest_release_data["tag_name"], cli_colors.ENDC))
    if show_version_only:
        return ExitCode.SUCCESS
    print("Build Name:", application_info("build_name"))
    print("Build:", application_info("build_number"))
    print("Supported platform:", scratch_info("platform"), scratch_info("platform_version"))
    print("\n" + "-"*80)
    print("Path Configuration")
    print("-"*80)
    for (option, entry) in config.items("PATHS"):
        not_exists = False
        for part in entry.split(":"):
            if not os.path.isfile(part) and not os.path.isdir(part):
                not_exists = True
                break
        exists_string = "NOT EXISTS" if not_exists else "EXISTS"
        exists_color = cli_colors.FAIL if not_exists else cli_colors.OKGREEN
        print("%s[%s]%s %s: %s" % (exists_color, exists_string, cli_colors.ENDC, option, os.path.normpath(entry)))

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
