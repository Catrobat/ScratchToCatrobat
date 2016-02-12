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
import ast
import sys
import os
import converterwebapp

from rq import Queue, use_connection
from converterjob import convert_scratch_project

sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "..", "src"))
from scratchtocatrobat.tools import helpers
import converterwebsocketprotocol as protocol

SCRATCH_PROJECT_BASE_URL = "https://scratch.mit.edu/projects/"
JOB_TIMEOUT = int(helpers.config.get("CONVERTER_JOB", "timeout"))
CATROBAT_FILE_EXT = helpers.config.get("CATROBAT", "file_extension")
REDIS_CLIENT_PROJECT_KEY = "clientsOfProject#{}"
REDIS_PROJECT_CLIENT_KEY = "projectsOfClient#{}"
REDIS_PROJECT_KEY = "project#{}"

_logger = logging.getLogger(__name__)

class Job(object):
    class Status:
        READY = 0
        RUNNING = 1
        FINISHED = 2
        FAILED = 3

    def __init__(self, jid=0, title=None, status=Status.READY, url=None,
                 progress=None, output=None):
        self.jid = jid
        self.title = title
        self.status = status
        self.url = url
        self.progress = progress
        self.output = output

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

class Command(object):
    def execute(self, ctxt, args):
        raise NotImplementedError()

    def is_valid_client_id(self, redis_connection, client_ID):
        client_ID_string = str(client_ID)
        last_client_ID = redis_connection.get("lastClientID")
        return last_client_ID != None and client_ID_string.isdigit() and int(client_ID_string) <= int(last_client_ID)

    def is_valid_scratch_project_url(self, scratch_project_url):
        if scratch_project_url is None or not isinstance(scratch_project_url, (str, unicode)):
            return False
        scratch_project_url = scratch_project_url.replace("http://", "https://")
        parts = [int(s) for s in scratch_project_url.split("/") if s.isdigit()]
        return scratch_project_url.startswith(SCRATCH_PROJECT_BASE_URL) and (len(parts) == 1)

    def retrieve_new_client_ID(self, ctxt):
        redis_conn = ctxt.redis_connection
        # check if this is the first client -> then set lastClientID in database to 0
        if redis_conn.get("lastClientID") == None:
            redis_conn.set("lastClientID", 0)
        new_client_ID = redis_conn.incr("lastClientID")
        ctxt.handler.set_client_ID(new_client_ID) # map client ID to web socket handler
        return new_client_ID

class RetrieveClientIDCommand(Command):
    def execute(self, ctxt, args):
        return protocol.ClientIDMessage(self.retrieve_new_client_ID(ctxt))

class SetClientIDCommand(Command):
    def execute(self, ctxt, args):
        if not self.is_valid_client_id(ctxt.redis_connection, args["clientID"]):
            return protocol.RenewClientIDMessage(self.retrieve_new_client_ID(ctxt))
        client_ID = int(args["clientID"])
        ctxt.handler.set_client_ID(client_ID) # map client ID to web socket handler
        update_jobs_info_on_listening_clients(ctxt)
        return protocol.ClientIDMessage(client_ID)

class RetrieveJobsInfoCommand(Command):
    def execute(self, ctxt, args):
        if not self.is_valid_client_id(ctxt.redis_connection, args["clientID"]):
            return protocol.ErrorMessage("Invalid client ID!")

        redis_conn = ctxt.redis_connection
        client_ID_string = str(args["clientID"])
        project_client_key = REDIS_PROJECT_CLIENT_KEY.format(client_ID_string)
        projects_of_client = redis_conn.get(project_client_key)
        projects_of_client = ast.literal_eval(projects_of_client) if projects_of_client != None else []
        assert isinstance(projects_of_client, list)
        jobs_info = []
        for scratch_project_ID in projects_of_client:
            project_key = REDIS_PROJECT_KEY.format(scratch_project_ID)
            job = Job.from_redis(redis_conn, project_key)
            if job == None:
                _logger.warn("Ignoring missing job for scratch project ID {}".format(scratch_project_ID))
                continue
            jobs_info += [job.__dict__]
        return protocol.JobsInfoMessage(jobs_info)

# TODO: create new packet for this and only send updates...
def update_jobs_info_on_listening_clients(ctxt):
    for client_ID, handler_list in converterwebapp.ConverterWebSocketHandler.client_ID_open_sockets_map.iteritems():
        message = RetrieveJobsInfoCommand().execute(ctxt, { "clientID": str(client_ID) })
        for handler in handler_list:
            handler.send_message(message)

class ScheduleJobCommand(Command):
    def execute(self, ctxt, args):
        def map_client_to_project(redis_connection, client_ID, scratch_project_ID):
            client_project_key = REDIS_CLIENT_PROJECT_KEY.format(scratch_project_ID)
            clients_of_project = redis_connection.get(client_project_key)
            if clients_of_project == None:
                clients_of_project = []
            else:
                clients_of_project = ast.literal_eval(clients_of_project)

            assert isinstance(clients_of_project, list)
            if client_ID not in clients_of_project:
                clients_of_project.append(client_ID)
                redis_connection.set(client_project_key, clients_of_project)

        def map_project_to_client(redis_connection, scratch_project_ID, client_ID):
            project_client_key = REDIS_PROJECT_CLIENT_KEY.format(client_ID)
            projects_of_client = redis_connection.get(project_client_key)
            if projects_of_client == None:
                projects_of_client = []
            else:
                projects_of_client = ast.literal_eval(projects_of_client)

            assert isinstance(projects_of_client, list)
            if scratch_project_ID not in projects_of_client:
                projects_of_client.append(scratch_project_ID)
                return redis_connection.set(project_client_key, projects_of_client)
            return True

        # validate parameters
        if not self.is_valid_client_id(ctxt.redis_connection, args["clientID"]):
            return protocol.ErrorMessage("Invalid client ID!")

        if not self.is_valid_scratch_project_url(args["url"]):
            return protocol.ErrorMessage("Invalid URL given!")

        # parameters
        client_ID_string = str(args["clientID"])
        scratch_project_url = args["url"].replace("http://", "https://")

        # reconstruct URL
        scratch_project_ID = [int(s) for s in scratch_project_url.split("/") if s.isdigit()][0]
        scratch_project_url = "%s%d" % (SCRATCH_PROJECT_BASE_URL, scratch_project_ID)

        # schedule this job
        redis_conn = ctxt.redis_connection
        # TODO: lock.acquire() => use "with" and file lock!
        map_client_to_project(redis_conn, client_ID_string, scratch_project_ID)
        map_project_to_client(redis_conn, scratch_project_ID, client_ID_string)
        project_key = REDIS_PROJECT_KEY.format(scratch_project_ID)
        job = Job.from_redis(redis_conn, project_key)
        jobmonitorserver_settings = ctxt.jobmonitorserver_settings
        if job != None:
            if job.status == Job.Status.READY or job.status == Job.Status.RUNNING:
                # TODO: lock.release()
                update_jobs_info_on_listening_clients(ctxt)
                return protocol.JobAlreadyRunningMessage(scratch_project_ID)
            elif job.status == Job.Status.FINISHED:
                download_dir = ctxt.jobmonitorserver_settings["download_dir"]
                file_name = str(scratch_project_ID) + CATROBAT_FILE_EXT
                file_path = "%s/%s" % (download_dir, file_name)
                if file_name and os.path.exists(file_path):
                    download_url = "/download?id=" + str(scratch_project_ID)
                    # TODO: lock.release()
                    update_jobs_info_on_listening_clients(ctxt)
                    return protocol.JobDownloadMessage(scratch_project_ID, download_url)
            else:
                assert job.status == Job.Status.FAILED

        job = Job(scratch_project_ID, "-", Job.Status.READY, scratch_project_url, 0.0)
        if not job.save_to_redis(redis_conn, project_key):
            # TODO: lock.release()
            return protocol.ErrorMessage("Cannot schedule job!")
        update_jobs_info_on_listening_clients(ctxt)

        use_connection(redis_conn)
        q = Queue(connection=redis_conn)
        host = jobmonitorserver_settings["host"]
        port = jobmonitorserver_settings["port"]
        #q.enqueue(convert_scratch_project, scratch_project_ID, host, port)
        q.enqueue_call(func=convert_scratch_project, args=(scratch_project_ID, host, port,), timeout=JOB_TIMEOUT)
        # TODO: lock.release()
        return protocol.JobReadyMessage(scratch_project_ID)

class InvalidCommand(Command):
    def execute(self, ctxt, args):
        return protocol.ErrorMessage("Invalid command!")

COMMANDS = {
    'retrieve_client_ID': RetrieveClientIDCommand(),
    'set_client_ID': SetClientIDCommand(),
    'retrieve_jobs_info': RetrieveJobsInfoCommand(),
    'schedule_job': ScheduleJobCommand()
}

def get_command(name):
    if not isinstance(name, (str, unicode)) or name not in COMMANDS:
        command = InvalidCommand()
    else:
        command = COMMANDS[name]
    return command
