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

import string
import logging

from redis import Redis
from rq import Queue, use_connection
from converterjob import convert_scratch_project

class ResultType:
    ERROR, WARNING, INFO = range(3)

class Result:
    def __init__(self, type, message):
        self.type = type
        self.message = message

class Command(object):
    def execute(self, args = {}):
        raise NotImplementedError()

class StartCommand(Command):
    def execute(self, args = {}):
        # validate scratch project url
        scratch_url = args["url"]
        if scratch_url is None or not isinstance(scratch_url, (str, unicode)) \
        or (not scratch_url.startswith("http://scratch.mit.edu/projects/") \
            and not scratch_url.startswith("https://scratch.mit.edu/projects/") \
        ):
            return Result(ResultType.ERROR, "No or invalid URL given")

        # schedule this job
        # TODO: check if redis is available => error!
        redis_connection = Redis() #'127.0.0.1', 6789) #, password='secret')
        use_connection(redis_connection)
        q = Queue(connection=redis_connection)
        q.enqueue(convert_scratch_project, scratch_url, args["host"], args["port"])
        return Result(ResultType.INFO, "Successfully scheduled job!")

class StopCommand(Command):
    def execute(self, args = {}):
        return Result(ResultType.ERROR, "NOT IMPLEMENTED")

class InvalidCommand(Command):
    def execute(self, args = {}):
        return Result(ResultType.ERROR, "Invalid command")

COMMANDS = {
    'start': StartCommand(),
    'stop': StopCommand()
}

def get_command(name):
    if not isinstance(name, (str, unicode)) or name not in COMMANDS:
        command = InvalidCommand()
    else:
        command = COMMANDS[name]
    return command
