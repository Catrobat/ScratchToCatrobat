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

from __future__ import print_function
import os
import sys
import time
import threading
import ConfigParser
import re
import urllib2, json
import progressbar
import hashlib
from functools import wraps

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
        self.config_parser = ConfigParser.ConfigParser()
    def read(self, filenames):
        result = self.config_parser.read(filenames)
        self.section_items = {}
        for section in self.config_parser.sections():
            items = {}
            for key, value in self.config_parser.items(section):
                items[key] = value
            self.section_items[section] = items
        return result
    def _populate_placeholders_of_entry(self, entry, section, option):
        entry = entry.replace("${APP_PATH}", APP_PATH)
        entry = entry.replace("${LIB_PATH}", LIB_PATH)
        entry = entry.replace("${SRC_PATH}", SRC_PATH)
        entry = entry.replace("${CFG_PATH}", CFG_PATH)
        regex = re.compile(r'\$\{([^\}]*)\}')
        if len(regex.findall(entry)) > 0:
            error("Unexpected placeholder token found in helpers file (section: %s, option: %s)!" % (section, option))
        return entry
    def items(self, section):
        items = self.section_items[section]
        return [(option, self._populate_placeholders_of_entry(entry, section, option)) for (option, entry) in items.iteritems()]
    def items_as_dict(self, section):
        items = self.section_items[section]
        result = {}
        for (option, entry) in items.iteritems():
            entry = self._populate_placeholders_of_entry(entry, section, option)
            keys = option.split(".")
            if len(keys) == 3 and keys[1].isdigit():
                if keys[0] not in result:
                    result[keys[0]] = {}
                if keys[1] not in result[keys[0]]:
                    result[keys[0]][keys[1]] = {}
                result[keys[0]][keys[1]][keys[2]] = entry
            else:
                result[option] = entry
        new_result = {}
        for (option, entry) in result.iteritems():
            if isinstance(entry, dict):
                new_result[option] = []
                for (_, element) in entry.iteritems():
                    new_result[option].append(element)
            else:
                new_result[option] = entry
        return new_result
    def get(self, section, option):
        options = [option] if type(option) is not list else option
        result = []
        for option in options:
            assert isinstance(option, (str, unicode))
            item = self.section_items[section][option]
            result += [self._populate_placeholders_of_entry(item, section, option)]
        return result if len(result) > 1 else result[0]
    def sections(self):
        return self.section_items.keys()

class ExitCode(object):
    SUCCESS = 0
    FAILURE = 1

def error(msg):
    print("ERROR: {0}".format(msg))
    sys.exit(ExitCode.FAILURE)

def make_dir_if_not_exists(path):
    paths = [path] if type(path) is not list else path
    for path in paths:
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
            response = urllib2.urlopen(url);
            json_data = response.read()

        latest_release_data = json.loads(json_data)
        with open(cached_file_path, 'w') as outfile:
            outfile.write(json_data)
        return latest_release_data
    except Exception:
        return None

def extract_version_number(version_str):
    parts = version_str.replace("v", "").split(".")
    return float("%s.%s" % (parts[0], ''.join(parts[1:]))) if len(parts) > 1 else float(version_str)

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
        current_release_version = extract_version_number(tag_name)
        latest_release_version = extract_version_number(latest_release_data["tag_name"])
        print("Latest Catroid release: %s (%s)" % (latest_release_data["tag_name"], latest_release_data["published_at"]))
        if current_release_version < latest_release_version:
            print("%sA NEW CATROID RELEASE IS AVAILABLE!\nPLEASE UPDATE THE CLASS HIERARCHY " \
                  "OF THE CONVERTER FROM CATROID VERSION %s TO VERSION %s%s" \
                  % (cli_colors.FAIL, tag_name, latest_release_data["tag_name"], cli_colors.ENDC))
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
    config.read(config_default_file_path)
    if os.path.exists(config_custom_env_file_path):
        if os.path.isdir(config_custom_env_file_path):
            error("Config file '%s' should be file, but is a directory!" % CFG_CUSTOM_ENV_FILE_NAME)
        if not os.access(config_custom_env_file_path, os.R_OK):
            error("No file permissions to read helpers file '%s'!" % CFG_CUSTOM_ENV_FILE_NAME)
        config_env = CatrobatConfigParser()
        config_env.read(config_custom_env_file_path)
        # merge both config files together
        for section in config.sections():
            if section not in config_env.sections():
                config_env.section_items[section] = config.section_items[section]
            else:
                merged_section = config.section_items[section]
                merged_section.update(config_env.section_items[section])
                config_env.section_items[section] = merged_section
        config = config_env
    return config

def inject_git_commmit_hook():
    git_dir = os.path.join(APP_PATH, ".git")
    if not os.path.isdir(git_dir): # abort, this seems to be no valid git repository...
        return

    hook_dir_path = os.path.join(git_dir, "hooks")
    make_dir_if_not_exists(hook_dir_path)
    hook_path = os.path.join(hook_dir_path, "pre-commit")

    config_default_file_path = os.path.normpath(os.path.join(CFG_PATH, CFG_DEFAULT_FILE_NAME))
    config_custom_env_file_path = os.path.normpath(os.path.join(CFG_PATH, CFG_CUSTOM_ENV_FILE_NAME))

    def formatted_shell_script_code(content):
        lines = content.split('\n')
        formatted_lines = []
        ignore_line_indentation = False
        python_code_line_indentation = -1
        update_python_code_line_indentation = False
        for line in lines[1:]: # skip first line
            if "<<EOF" in line:
                ignore_line_indentation = True
            elif "EOF" in line:
                ignore_line_indentation = False
            if update_python_code_line_indentation:
                index = 0
                for c in line:
                    if c is not " ":
                        break
                    index += 1
                update_python_code_line_indentation = False
                python_code_line_indentation = index
            if ignore_line_indentation and python_code_line_indentation != -1:
                line = line[python_code_line_indentation:]
            else:
                line = line.lstrip()
            formatted_lines.append(line + '\n')
            if ignore_line_indentation and python_code_line_indentation == -1:
                update_python_code_line_indentation = True
        return ''.join(formatted_lines)

    shell_script_code = """
        #!/bin/sh
        PROJECT_DIR=`pwd`
        CONFIG_DEFAULT_FILE_PATH="%s"
        CONFIG_CUSTOM_ENV_FILE_PATH="%s"
        branchName=`/usr/bin/env git symbolic-ref HEAD | sed -e 's,.*/\\(.*\\),\\1,'`
        gitCount=`/usr/bin/env git rev-list $branchName |wc -l | sed 's/^ *//;s/ *$//'`
        simpleBranchName=`/usr/bin/env git rev-parse --abbrev-ref HEAD`
        buildNumber="$((gitCount + 1))"
        buildNumber+="-$simpleBranchName"

        /usr/bin/env python - <<EOF
            def update_build_number(config_file_name, number):
                # TODO: regex...
                content = open(config_file_name).read()
                search_str = "build_number:"
                start_pos = content.find(search_str)
                if start_pos == -1:
                    return # not found...
                else:
                    start_pos += len(search_str)
                end_pos = content.find("\\n", start_pos)
                old_build_no_str = "{0}{1}".format(search_str, content[start_pos:end_pos])
                new_build_no_str = "{0}  {1}".format(search_str, number)
                content = content.replace(old_build_no_str, new_build_no_str)
                with open(config_file_name, 'w') as config_file:
                    config_file.write(content)
            update_build_number("${CONFIG_DEFAULT_FILE_PATH}", "${buildNumber}")
            import os
            if os.path.isfile("${CONFIG_CUSTOM_ENV_FILE_PATH}"):
                update_build_number("${CONFIG_CUSTOM_ENV_FILE_PATH}", "${buildNumber}")
        EOF

        # Add modified config file to the staging area
        # NOTE: Only the default config file is part of the repository!
        cd ${PROJECT_DIR}
        if [ -f "$CONFIG_DEFAULT_FILE_PATH" ]; then
        /usr/bin/env git add ${CONFIG_DEFAULT_FILE_PATH}
        fi
        exit 0
    """ % (config_default_file_path, config_custom_env_file_path)

    formatted_shell_script_code = formatted_shell_script_code(shell_script_code)
    with open(hook_path, "w") as shell_script_file:
        shell_script_file.write(formatted_shell_script_code)
    os.chmod(hook_path, 0755)

config = _setup_configuration()

JYTHON_RESPECT_JAVA_ACCESSIBILITY_PROPERTY = "python.security.respectJavaAccessibility"

# based on: http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
def retry(ExceptionsToCheck, tries=4, delay=2, backoff=2, hook=None):
    """Retry calling the decorated function using an exponential backoff.
    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    """
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while True:
                try:
                    return f(*args, **kwargs)
                except ExceptionsToCheck as e:
                    if mtries > 0:
                        if hook:
                            hook(e, mtries, mdelay)
                        time.sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff
                    else:
                        raise e
        return f_retry  # true decorator
    return deco_retry

def isfloat(string):
    try:
        number = float(string) # @UnusedVariable
    except ValueError:
        return False
    else:
        return True

def md5_of_file(file_path):
    file_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            file_hash.update(chunk)
    return file_hash.hexdigest()


class ProgressType(object):
    DOWNLOAD_CODE = 1
    DOWNLOAD_MEDIA_FILE = 2
    DETAILS = 3
    CONVERT_MEDIA_FILE = 4
    CONVERT_SCRIPT = 5
    SAVE_XML = 6

class Progress(object):
    def __init__(self, download_code_iterations=0, details_iterations=0,
                 download_media_file_iterations=0, convert_media_file_iterations=0,
                 convert_script_iterations=0, save_xml_iterations=0):
        self.iterations = {
            ProgressType.DOWNLOAD_CODE:          download_code_iterations,
            ProgressType.DETAILS:                details_iterations,
            ProgressType.DOWNLOAD_MEDIA_FILE:    download_media_file_iterations,
            ProgressType.CONVERT_MEDIA_FILE:     convert_media_file_iterations,
            ProgressType.CONVERT_SCRIPT:         convert_script_iterations,
            ProgressType.SAVE_XML:               save_xml_iterations
        }

    def sum(self):
        return sum(self.iterations.values())

    def __str__(self):
        return str(self.iterations)


class ProgressBar(object):

    SAVING_XML_PROGRESS_WEIGHT_PERCENTAGE = 3
    START_PROGRESS_INDICATOR = "#__("
    END_PROGRESS_INDICATOR = "%)__"

    def __init__(self, expected_progress, web_mode=False, output_stream=sys.stdout):
        self._iterations = Progress()
        self.expected_progress = expected_progress
        self._output_stream = output_stream
        self.lock = threading.RLock()
        self.saving_xml_progress_weight = 0
        self.web_mode = web_mode
        self.finished = False
        widgets = [progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()]
        if not self.web_mode:
            self.pbar = progressbar.ProgressBar(widgets=widgets, maxval=100)
            self.pbar.start()

    def finish(self):
        with self.lock:
            if self.finished:
                return
            self.finished = True
            if not self.web_mode:
                self.pbar.finish()
            # TODO: fix this...
            #assert self.is_full() # Note: reentrant lock! no deadlock can happen here!

    def is_full(self):
        with self.lock:
            return self._iterations.sum() == self.expected_progress.sum()

    def update(self, progress_type, increment=1):
        with self.lock:
            if increment == 0:
                return

            if self.expected_progress == None:
                if self._output_stream != None:
                    self._output_stream.write("[WARNING] Iterations not set!")
                return

            iterations_counter = self._iterations.iterations[progress_type]
            expected_iterations = self.expected_progress.iterations[progress_type]
            if iterations_counter + increment > expected_iterations:
                if self._output_stream != None:
                    self._output_stream.write("[WARNING] Progress counter overflow for type %d!"
                                              % progress_type)
                return

            self._iterations.iterations[progress_type] += increment
            percentage = float(self._iterations.sum()) / float(self.expected_progress.sum()) * 100.0

            if not self.web_mode:
                self.pbar.update(int(round(percentage)))
                return

            if self._output_stream == None:
                return

            self._output_stream.write("{}{}{}\n".format(ProgressBar.START_PROGRESS_INDICATOR, \
                                                      round(percentage, 2), \
                                                      ProgressBar.END_PROGRESS_INDICATOR))
