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
from command import Command
from websocketserver.protocol.message.base.error_message import ErrorMessage
from websocketserver.protocol.message.base.jobs_info_message import JobsInfoMessage
from websocketserver.protocol.job import Job
import helpers as webhelpers

_logger = logging.getLogger(__name__)


class RetrieveJobsInfoCommand(Command):

    def execute(self, ctxt, args):
        client_ID = args[Command.ArgumentType.CLIENT_ID]
        if not self.is_valid_client_ID(ctxt.redis_connection, client_ID):
            return ErrorMessage("Invalid client ID!")

        redis_conn = ctxt.redis_connection
        job_client_key = webhelpers.REDIS_JOB_CLIENT_KEY_TEMPLATE.format(client_ID)
        jobs_of_client = redis_conn.get(job_client_key)
        jobs_of_client = ast.literal_eval(jobs_of_client) if jobs_of_client != None else []
        assert isinstance(jobs_of_client, list)
        jobs_info = []
        for job_ID in jobs_of_client:
            project_key = webhelpers.REDIS_JOB_KEY_TEMPLATE.format(job_ID)
            job = Job.from_redis(redis_conn, project_key)
            if job == None:
                _logger.warn("Ignoring missing job for scratch project ID {}".format(job_ID))
                continue
            info = job.__dict__
            del info["output"]
            jobs_info += [info]
        return JobsInfoMessage(jobs_info)
