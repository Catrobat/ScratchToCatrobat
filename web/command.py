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

from rq import Queue, use_connection
from converterjob import convert_scratch_project

sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "..", "src"))
from scratchtocatrobat.tools import helpers

SCRATCH_PROJECT_BASE_URL = "https://scratch.mit.edu/projects/"
JOB_TIMEOUT = int(helpers.config.get("CONVERTER_JOB", "timeout"))

class Result:
    class Status:
        ERROR = 0
        SUCCESS = 1

    def __init__(self, status, data):
        self.status = status
        self.data = data

class Job:
    class Status:
        READY = 0
        RUNNING = 1
        FINISHED = 2
        FAILED = 3

    def __init__(self, status, progress=None, url=None):
        self.status = status
        self.progress = progress
        self.url = url

    def save_to_redis(self, redis_connection, key):
        return redis_connection.set(key, self.__dict__)

    @classmethod
    def from_redis(cls, redis_connection, key):
        dict_string = redis_connection.get(key)
        if dict_string == None:
            return None
        job = cls(Job.Status.READY)
        for (key, value) in ast.literal_eval(dict_string).items():
            setattr(job, key, value)
        return job

class Command(object):
    def execute(self, ctxt, args):
        raise NotImplementedError()

class RetrieveClientIDCommand(Command):
    def execute(self, ctxt, args):
        redis_conn = ctxt.redis_connection
        last_client_ID = redis_conn.get("lastClientID")
        if last_client_ID == None: redis_conn.set("lastClientID", 0)
        new_client_ID = redis_conn.incr("lastClientID")
        ctxt.handler.set_client_ID(new_client_ID) # map client ID to web socket handler
        return Result(Result.Status.SUCCESS, { "clientID": new_client_ID })

class StartCommand(Command):
    def execute(self, ctxt, args):

        def map_client_to_project(redis_connection, client_ID, scratch_project_ID):
            REDIS_CLIENT_PROJECT_KEY = "clientsOfProject#{}".format(scratch_project_ID)
            clients_of_project = redis_connection.get(REDIS_CLIENT_PROJECT_KEY)
            if clients_of_project == None:
                clients_of_project = []
            else:
                clients_of_project = ast.literal_eval(clients_of_project)

            if client_ID not in clients_of_project:
                clients_of_project.append(client_ID)
                redis_connection.set(REDIS_CLIENT_PROJECT_KEY, clients_of_project)

        def map_project_to_client(redis_connection, scratch_project_ID, client_ID):
            REDIS_PROJECT_CLIENT_KEY = "projectsOfClient#{}".format(client_ID)
            projects_of_client = redis_connection.get(REDIS_PROJECT_CLIENT_KEY)
            if projects_of_client == None:
                projects_of_client = []
            else:
                projects_of_client = ast.literal_eval(projects_of_client)

            if scratch_project_ID not in projects_of_client:
                projects_of_client.append(scratch_project_ID)
                return redis_connection.set(REDIS_PROJECT_CLIENT_KEY, projects_of_client)
            return True

        scratch_project_url = args["url"]
        client_ID = str(args["clientID"])
        if scratch_project_url is None or not isinstance(scratch_project_url, (str, unicode)):
            return Result(Result.Status.ERROR, { "msg": "No or invalid URL given" })
        if client_ID is None or not isinstance(client_ID, (str, unicode)) or not client_ID.isdigit():
            return Result(Result.Status.ERROR, { "msg": "No or invalid URL given" })

        # validate URL
        scratch_project_url = scratch_project_url.replace("http://", "https://")
        parts = [int(s) for s in scratch_project_url.split("/") if s.isdigit()]
        if not scratch_project_url.startswith(SCRATCH_PROJECT_BASE_URL) or (len(parts) != 1):
            return Result(Result.Status.ERROR, { "msg": "Invalid URL given" })

        # reconstruct URL
        scratch_project_ID = parts[0]
        scratch_project_url = "%s%d" % (SCRATCH_PROJECT_BASE_URL, scratch_project_ID)

        REDIS_PROJECT_KEY = "project#{}".format(scratch_project_ID)

        # schedule this job
        redis_conn = ctxt.redis_connection
        # TODO: lock.acquire() => use "with" and file lock!
        map_client_to_project(redis_conn, client_ID, scratch_project_ID)
        map_project_to_client(redis_conn, scratch_project_ID, client_ID)
        job = Job.from_redis(redis_conn, REDIS_PROJECT_KEY)
        jobmonitorserver_settings = ctxt.jobmonitorserver_settings
        if job != None:
            if job.status == Job.Status.READY or job.status == Job.Status.RUNNING:
                # TODO: lock.release()
                return Result(Result.Status.SUCCESS, { "msg": "Job already scheduled!" })
            elif job.status == Job.Status.FINISHED:
                download_url = "/download?id=" + str(scratch_project_ID)
                # TODO: lock.release()
                return Result(Result.Status.SUCCESS, { "url": download_url })

        job = Job(Job.Status.READY)
        if not job.save_to_redis(redis_conn, REDIS_PROJECT_KEY):
            # TODO: lock.release()
            return Result(Result.Status.ERROR, { "msg": "Cannot schedule job!" })

        use_connection(redis_conn)
        q = Queue(connection=redis_conn)
        host = jobmonitorserver_settings["host"]
        port = jobmonitorserver_settings["port"]
        #q.enqueue(convert_scratch_project, scratch_project_ID, host, port)
        print(JOB_TIMEOUT)
        print(type(JOB_TIMEOUT))
        q.enqueue_call(func=convert_scratch_project, args=(scratch_project_ID, host, port,), timeout=JOB_TIMEOUT)
        # TODO: lock.release()
        return Result(Result.Status.SUCCESS, { "msg": "Job successfully scheduled!" })

class StopCommand(Command):
    def execute(self, ctxt, args):
        return Result(ResultType.ERROR, "NOT IMPLEMENTED")

class InvalidCommand(Command):
    def execute(self, ctxt, args):
        return Result(ResultType.ERROR, "Invalid command")

COMMANDS = {
    'retrieve_client_ID': RetrieveClientIDCommand(),
    'start': StartCommand(),
    'stop': StopCommand()
}

def get_command(name):
    if not isinstance(name, (str, unicode)) or name not in COMMANDS:
        command = InvalidCommand()
    else:
        command = COMMANDS[name]
    return command
