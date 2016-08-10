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
import command
import os
import ast
from datetime import datetime as dt, timedelta
from rq import Queue, use_connection #@UnresolvedImport
from converterjob import convert_scratch_project
from websocketserver.protocol import protocol
from websocketserver.protocol.job import Job
from scratchtocatrobat.tools import helpers
import helpers as webhelpers

CATROBAT_FILE_EXT = helpers.config.get("CATROBAT", "file_extension")
SCRATCH_PROJECT_IMAGE_URL_TEMPLATE = helpers.config.get("SCRATCH_API", "project_image_url_template")
JOB_TIMEOUT = int(helpers.config.get("CONVERTER_JOB", "timeout"))

_logger = logging.getLogger(__name__)


def assign_client_to_job(redis_connection, client_ID, job_ID):
    client_job_key = webhelpers.REDIS_CLIENT_JOB_KEY_TEMPLATE.format(job_ID)
    clients_of_job = redis_connection.get(client_job_key)
    clients_of_job = ast.literal_eval(clients_of_job) if clients_of_job != None else []

    assert isinstance(clients_of_job, list)
    if client_ID not in clients_of_job:
        clients_of_job.append(client_ID)
        return redis_connection.set(client_job_key, clients_of_job)
    return True


def assign_job_to_client(redis_connection, scratch_project_ID, client_ID):
    job_client_key = webhelpers.REDIS_JOB_CLIENT_KEY_TEMPLATE.format(client_ID)
    jobs_of_client = redis_connection.get(job_client_key)
    jobs_of_client = ast.literal_eval(jobs_of_client) if jobs_of_client != None else []

    assert isinstance(jobs_of_client, list)
    if scratch_project_ID not in jobs_of_client:
        jobs_of_client.append(scratch_project_ID)
        return redis_connection.set(job_client_key, jobs_of_client)
    return True


class ScheduleJobCommand(command.Command):
    def execute(self, ctxt, args):
        # validate parameters
        if not self.is_valid_client_ID(ctxt.redis_connection, args["clientID"]):
            return protocol.ErrorMessage("Invalid client ID!")

        if not self.is_valid_job_ID(args["jobID"]):
            return protocol.ErrorMessage("Invalid jobID given!")

        force = False
        if "force" in args:
            force_param = str(args["force"]).lower()
            force = force_param == "true" or force_param == "1"

        # parameters
        client_ID_string = str(args["clientID"])
        job_ID = int(args["jobID"])

        verbose = False
        if "verbose" in args:
            verbose_param = str(args["verbose"]).lower()
            verbose = verbose_param == "true" or verbose_param == "1"

        # schedule this job
        redis_conn = ctxt.redis_connection
        # TODO: lock.acquire() => use context-handler (i.e. "with"-keyword) and file lock!
        assign_client_to_job(redis_conn, client_ID_string, job_ID)
        assign_job_to_client(redis_conn, job_ID, client_ID_string)
        job_key = webhelpers.REDIS_JOB_KEY_TEMPLATE.format(job_ID)
        job = Job.from_redis(redis_conn, job_key)
        jobmonitorserver_settings = ctxt.jobmonitorserver_settings

        if job != None:
            if job.status == Job.Status.READY or job.status == Job.Status.RUNNING:
                # TODO: lock.release()
                _logger.info("Job already scheduled (scratch project with ID: %d)", job_ID)
                return protocol.JobAlreadyRunningMessage(job_ID)
            elif job.status == Job.Status.FINISHED and not force:
                assert job.archiveCachedUTCDate is not None
                archive_cached_utc_date = dt.strptime(job.archiveCachedUTCDate, Job.DATETIME_FORMAT)
                download_valid_until_utc = archive_cached_utc_date + timedelta(seconds=Job.CACHE_ENTRY_VALID_FOR)

                if dt.utcnow() <= download_valid_until_utc:
                    file_name = str(job_ID) + CATROBAT_FILE_EXT
                    file_path = "%s/%s" % (ctxt.jobmonitorserver_settings["download_dir"], file_name)
                    if file_name and os.path.exists(file_path):
                        download_url = webhelpers.create_download_url(job_ID, job.title)
                        # TODO: lock.release()
                        return protocol.JobDownloadMessage(job_ID, download_url, job.archiveCachedUTCDate)

            else:
                assert job.status == Job.Status.FAILED or force

        job = Job(job_ID, "-", Job.Status.READY)
        if not job.save_to_redis(redis_conn, job_key):
            # TODO: lock.release()
            return protocol.ErrorMessage("Cannot schedule job!")

        use_connection(redis_conn)
        q = Queue(connection=redis_conn)
        host, port = jobmonitorserver_settings["host"], jobmonitorserver_settings["port"]
        _logger.info("Scheduled new job (host: %s, port: %s, scratch project ID: %d)", host, port, job_ID)
        #q.enqueue(convert_scratch_project, scratch_project_ID, host, port)
        q.enqueue_call(func=convert_scratch_project, args=(job_ID, host, port, verbose,), timeout=JOB_TIMEOUT)
        # TODO: lock.release()
        return protocol.JobReadyMessage(job_ID)
