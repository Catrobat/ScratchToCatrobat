#!/usr/bin/env python
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
import platform
import subprocess
import sys

################################################################################
#
# CONFIGURATION
#
################################################################################
JYTHON_HOME_PATH = "/Users/r4ll3/Development/Desktop/jython2.7b/"

################################################################################
#
# SETUP
#
################################################################################

APP_PATH = os.path.realpath(os.path.dirname(__file__))
LIB_PATH = os.path.join(APP_PATH, "lib")
SRC_PATH = os.path.join(APP_PATH, "src")

class ExitCode(object):
    SUCCESS = 0
    FAILURE = 1

env = os.environ
env['JYTHONPATH'] = env.get('JYTHONPATH') or APP_PATH + ':' + APP_PATH + '/src/scratchtocatrobat:' + LIB_PATH + '/catroid_class_hierarchy.jar:' + LIB_PATH + '/xmlpull-1.1.3.1.jar:' + LIB_PATH + '/xpp3_min-1.1.4c.jar:' + LIB_PATH + '/xstream-1.4.7.jar:' + SRC_PATH + ':' + LIB_PATH + '/batik-1.7/batik-rasterizer.jar'
env['JYTHON_HOME'] = env.get('JYTHON_HOME') or JYTHON_HOME_PATH
env['CLASSPATH'] = env.get('CLASSPATH') or '' + os.pathsep + LIB_PATH
env['BATIK_HOME'] = os.path.join(LIB_PATH, "batik-1.7")
env['JYTHON_STANDALONE_JAR'] = os.path.join(env.get('JYTHON_HOME'), "jython.jar")

def error(msg):
    print(msg)
    sys.exit(ExitCode.FAILURE)

jython_home = env.get('JYTHON_HOME')
if not jython_home:
    error("Environment variable 'JYTHON_HOME' must be set.")
jython_path = os.path.join(jython_home, "bin", "jython")
if platform.system().lower().startswith("win"):
    jython_path += ".bat"
if not os.path.exists(jython_path):
    error("Jython script path '%s' must exist.", jython_path.replace(".bat", "[.bat]"))
exec_args = [jython_path, "-m", "scratchtocatrobat.main"] + sys.argv[1:]
sys.exit(subprocess.call(exec_args, env=env))
