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
#
#  ---------------------------------------------------------------------------------------
#  NOTE:
#  ---------------------------------------------------------------------------------------
#  This module is a simple web socket server based on the Tornado web framework and
#  asynchronous networking library, which is licensed under the Apache License, Version 2.0.
#  For more information about the Apache License please visit:
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  For scheduling purposes the rq library (based on Redis) is used.
#  The rq library is licensed under the BSD License:
#
#    https://raw.github.com/nvie/rq/master/LICENSE
#

import logging, ast
import tornado.escape #@UnresolvedImport
import tornado.websocket #@UnresolvedImport
from protocol import protocol
from protocol.command import command as cmd
from protocol.job import Job
from protocol.message.message import Message
from protocol.message.job.job_download_message import JobDownloadMessage
from protocol.message.job.job_failed_message import JobFailedMessage
from protocol.message.job.job_finished_message import JobFinishedMessage
from protocol.message.job.job_output_message import JobOutputMessage
from protocol.message.job.job_progress_message import JobProgressMessage
from protocol.message.job.job_running_message import JobRunningMessage
import jobmonitorprotocol as jobmonprot
from jobmonitorprotocol import NotificationType
import helpers as webhelpers
import redis #@UnresolvedImport
from datetime import datetime as dt

_logger = logging.getLogger(__name__)
# TODO: check if redis is available => error!
_redis_conn = redis.Redis() #'127.0.0.1', 6789) #, password='secret')


class Context(object):
    def __init__(self, handler, redis_connection, jobmonitorserver_settings):
        self.handler = handler
        self.redis_connection = redis_connection
        self.jobmonitorserver_settings = jobmonitorserver_settings


class ConverterWebSocketHandler(tornado.websocket.WebSocketHandler):

    client_ID_open_sockets_map = {}

    def get_compression_options(self):
        return {} # Non-None enables compression with default options.

    def set_client_ID(self, client_ID):
        cls = self.__class__
        if client_ID not in cls.client_ID_open_sockets_map:
            cls.client_ID_open_sockets_map[client_ID] = []
        cls.client_ID_open_sockets_map[client_ID].append(self)

    @classmethod
    def notify(cls, msg_type, args):
        # Note: jobID is always equivalent to scratch project ID
        job_ID = args[jobmonprot.Request.ARGS_JOB_ID]
        job_key = webhelpers.REDIS_JOB_KEY_TEMPLATE.format(job_ID)
        client_job_key = webhelpers.REDIS_CLIENT_JOB_KEY_TEMPLATE.format(job_ID)
        job = Job.from_redis(_redis_conn, job_key)
        #old_status = job.status

        if job == None:
            _logger.error("Cannot find job #{}".format(job_ID))
            return

        if msg_type == NotificationType.JOB_STARTED:
            imageURL = args[jobmonprot.Request.ARGS_IMAGE_URL]
            job.title = args[jobmonprot.Request.ARGS_TITLE]
            job.imageURL = imageURL
            job.width, job.height = webhelpers.extract_width_and_height_from_scratch_image_url(imageURL, job_ID)
            job.status = Job.Status.RUNNING
        elif msg_type == NotificationType.JOB_FAILED:
            _logger.warn("Job failed! Exception Args: %s", args)
            job.status = Job.Status.FAILED
        elif msg_type == NotificationType.JOB_OUTPUT:
            if job.output == None: job.output = ""
            for line in args[jobmonprot.Request.ARGS_LINES]:
                job.output += line
        elif msg_type == NotificationType.JOB_PROGRESS:
            job.progress = args[jobmonprot.Request.ARGS_PROGRESS]
        elif msg_type == NotificationType.JOB_FINISHED:
            _logger.info("Job #{} finished, waiting for file transfer".format(job_ID))
        elif msg_type == NotificationType.FILE_TRANSFER_FINISHED:
            job.progress = 100.0
            job.status = Job.Status.FINISHED
            job.archiveCachedUTCDate = dt.utcnow().strftime(Job.DATETIME_FORMAT)
        if not job.save_to_redis(_redis_conn, job_key):
            _logger.info("Unable to update job status!")
            return

        # inform all clients if status or progress changed
        # TODO: refactor this!
        #if old_status != job.status or msg_type == NotificationType.JOB_PROGRESS:
        #    update_jobs_info_on_listening_clients(Context(None, _redis_conn, None))

        # find listening clients
        # TODO: cache this...
        clients_of_project = _redis_conn.get(client_job_key)
        if clients_of_project == None:
            _logger.warn("WTH?! No listening clients stored!")
            return

        clients_of_project = ast.literal_eval(clients_of_project)
        num_clients_of_project = len(clients_of_project)
        _logger.debug("There %s %d registered client%s." % \
                      ("is" if num_clients_of_project == 1 else "are", \
                       num_clients_of_project, "s" if num_clients_of_project != 1 else ""))
        listening_clients = [cls.client_ID_open_sockets_map[int(client_ID)] for client_ID in clients_of_project if int(client_ID) in cls.client_ID_open_sockets_map]
        _logger.debug("There are %d active clients listening on this job." % len(listening_clients))

        for socket_handlers in listening_clients:
            if msg_type == NotificationType.JOB_STARTED:
                message = JobRunningMessage(job_ID)
            elif msg_type == NotificationType.JOB_OUTPUT:
                message = JobOutputMessage(job_ID, args[jobmonprot.Request.ARGS_LINES])
            elif msg_type == NotificationType.JOB_PROGRESS:
                message = JobProgressMessage(job_ID, args[jobmonprot.Request.ARGS_PROGRESS])
            elif msg_type == NotificationType.JOB_FINISHED:
                message = JobFinishedMessage(job_ID)
            elif msg_type == NotificationType.FILE_TRANSFER_FINISHED:
                download_url = webhelpers.create_download_url(job_ID, job.title)
                message = JobDownloadMessage(job_ID, download_url, None)
            elif msg_type == NotificationType.JOB_FAILED:
                message = JobFailedMessage(job_ID)
            else:
                _logger.warn("IGNORING UNKNOWN MESSAGE")
                return
            for handler in socket_handlers:
                handler.send_message(message)

    def on_close(self):
        cls = self.__class__
        _logger.info("Closing WebSocket")
        for (client_ID, open_sockets) in cls.client_ID_open_sockets_map.iteritems():
            if self in open_sockets:
                open_sockets.remove(self)
                if len(open_sockets) == 0:
                    del cls.client_ID_open_sockets_map[client_ID]
                else:
                    cls.client_ID_open_sockets_map[client_ID] = open_sockets
                _logger.info("Found WebSocket and closed it")
                return # break out of loop => limit is 1 socket/clientID

    def send_message(self, message):
        assert isinstance(message, Message)
        _logger.debug("Sending %s %r to %d", message.__class__.__name__, message.as_dict(), id(self))
        try:
            self.write_message(tornado.escape.json_encode(message.as_dict()))
        except:
            _logger.error("Error sending message", exc_info=True)

    def on_message(self, message):
        _logger.debug("Received message %r", message)
        data = tornado.escape.json_decode(message)
        args = {}
        if protocol.JsonKeys.Request.is_valid(data):
            command = cmd.get_command(data[protocol.JsonKeys.Request.CMD])
            args = protocol.JsonKeys.Request.extract_allowed_args(data[protocol.JsonKeys.Request.ARGS])
        else:
            command = cmd.InvalidCommand()
        # TODO: when client ID is given => check if it belongs to socket handler!
        redis_conn = _redis_conn
        ctxt = Context(self, redis_conn, self.application.settings["jobmonitorserver"])
        _logger.info("Executing command %s", command.__class__.__name__)
        self.send_message(command.execute(ctxt, args))
