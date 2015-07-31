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
import logging
import os
from datetime import datetime

log = logging.getLogger("scratchtocatrobat")

def initialize_logging():
    log.setLevel(logging.DEBUG)

    APP_PATH = os.path.realpath(os.path.dirname(__file__))
    fh = logging.FileHandler(os.path.join(APP_PATH, '..', '..', 'data', 'log', "s2cc-{}.log".format(datetime.now().isoformat().replace(":", "_"))))
    fh_fmt = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s (%(filename)s:%(lineno)s)")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fh_fmt)
    log.addHandler(fh)

    ch = logging.StreamHandler()
    ch_fmt = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
    ch.setLevel(logging.INFO)
    ch.setFormatter(ch_fmt)
    log.addHandler(ch)

    log.debug("Logging initialized")
