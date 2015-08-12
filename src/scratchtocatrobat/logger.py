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
import logging

log = logging.getLogger("scratchtocatrobat")

def _log_level_for_string(log_level_string):
    if log_level_string == "FATAL":
        return logging.FATAL
    elif log_level_string == "CRITICAL":
        return logging.CRITICAL
    elif log_level_string == "ERROR":
        return logging.ERROR
    elif log_level_string == "WARNING" or log_level_string == "WARN":
        return logging.WARN
    elif log_level_string == "INFO":
        return logging.INFO
    elif log_level_string == "DEBUG":
        return logging.DEBUG
    else:
        return logging.INFO

def setup_logging():
    import os
    from datetime import datetime
    from tools import helpers
    log.setLevel(logging.DEBUG)

    log_dir = helpers.config.get("PATHS", "logging")
    fh = logging.FileHandler(os.path.join(log_dir, "s2cc-{}.log".format(datetime.now().isoformat().replace(":", "_"))))
    fh_fmt = logging.Formatter(helpers.config.get("LOG", "file_log_format").replace("\\", ""))

    fh.setLevel(_log_level_for_string(helpers.config.get("LOG", "file_log_level")))
    fh.setFormatter(fh_fmt)
    log.addHandler(fh)

    ch = logging.StreamHandler()
    ch_fmt = logging.Formatter(helpers.config.get("LOG", "stdout_log_format").replace("\\", ""))
    ch.setLevel(_log_level_for_string(helpers.config.get("LOG", "stdout_log_level")))
    ch.setFormatter(ch_fmt)
    log.addHandler(ch)
    log.debug("Logging initialized")
