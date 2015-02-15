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

project_home = os.path.realpath(os.path.dirname(__file__))
library_path = os.path.join(project_home, "lib")

env = os.environ
new_jythonpath = os.path.join(project_home, "src")
env['JYTHONPATH'] = env.get('JYTHONPATH') or '' + os.pathsep + new_jythonpath
env['CLASSPATH'] = env.get('CLASSPATH') or '' + os.pathsep + library_path
env['BATIK_HOME'] = os.path.join(library_path, "batik-1.7")

jython_home = env.get('JYTHON_HOME')
if not jython_home:
    error("Environment vairable 'JYTHON_HOME' must be set.")
jython_path = os.path.join(jython_home, "jython")
if platform.system().lower().startswith("win"):
    jython_path += ".bat"
if not os.path.exists(jython_path):
    error("Jython script path '%s' must exist.", jython_path.replace(".bat", "[.bat]"))
exec_args = [jython_path, "-m", "scratchtocatrobat.main"] + sys.argv[1:]
sys.exit(subprocess.call(exec_args, env=env))

