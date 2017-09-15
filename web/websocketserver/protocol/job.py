#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2016 The Catrobat Team
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
import ast

_logger = logging.getLogger(__name__)


class Job(object):
    class State(object):
        READY = 0
        RUNNING = 1
        FINISHED = 2
        FAILED = 3


    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    CACHE_ENTRY_VALID_FOR = 600

    def __init__(self, job_ID=0, title=None, state=State.READY, progress=0, output=None,
                 image_url=None, archive_cached_utc_date=None):
        self.jobID = job_ID
        self.title = title
        self.state = state
        self.progress = progress
        self.output = output
        self.imageURL = image_url
        self.archiveCachedUTCDate = archive_cached_utc_date


    def is_in_progress(self):
        return self.state in (Job.State.READY, Job.State.RUNNING)


    def save_to_redis(self, redis_connection, key):
        return redis_connection.set(key, self.__dict__)


    @classmethod
    def from_redis(cls, redis_connection, key):
        dict_string = redis_connection.get(key)
        if dict_string == None:
            return None
        job = cls()
        for (key, value) in ast.literal_eval(dict_string).items():
            setattr(job, key, value)
        return job

