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

import logging
import ast
import json
import tornado.escape
import tornado.websocket
from protocol import protocol
from protocol.command import command as cmd
from protocol.command.schedule_job_command import remove_all_listening_clients_from_job
from protocol.job import Job
from protocol.message.message import Message
from protocol.message.job.job_failed_message import JobFailedMessage
from protocol.message.job.job_finished_message import JobFinishedMessage
from protocol.message.job.job_output_message import JobOutputMessage
from protocol.message.job.job_progress_message import JobProgressMessage
from protocol.message.job.job_running_message import JobRunningMessage
from jobmonitorserver import jobmonitorprotocol as jobmonprot
from jobmonitorserver.jobmonitorprotocol import NotificationType
import helpers as webhelpers
from datetime import datetime as dt

_logger = logging.getLogger(__name__)


class Context(object):
    def __init__(self, handler, redis_connection, jobmonitorserver_settings):
        self.handler = handler
        self.redis_connection = redis_connection
        self.jobmonitorserver_settings = jobmonitorserver_settings


class ConverterWebSocketHandler(tornado.websocket.WebSocketHandler):

    REDIS_CONNECTION = None
    client_ID_open_sockets_map = {}

    def get_compression_options(self):
        return {} # Non-None enables compression with default options.


    def set_client_ID(self, client_ID):
        assert isinstance(client_ID, int)
        cls = self.__class__
        if client_ID not in cls.client_ID_open_sockets_map:
            cls.client_ID_open_sockets_map[client_ID] = []
        cls.client_ID_open_sockets_map[client_ID].append(self)


    def get_client_ID(self):
        cls = self.__class__
        for (client_ID, open_sockets) in cls.client_ID_open_sockets_map.iteritems():
            if self in open_sockets:
                return client_ID # 1 clientID per socket
        return None


    @classmethod
    def notify(cls, msg_type, args):
        # Note: jobID is equivalent to scratch project ID by definition!
        job_ID = args[jobmonprot.Request.ARGS_JOB_ID]
        job_key = webhelpers.REDIS_JOB_KEY_TEMPLATE.format(job_ID)
        job = Job.from_redis(cls.REDIS_CONNECTION, job_key)

        if job == None:
            _logger.error("Cannot find job #{}".format(job_ID))
            return

        if msg_type == NotificationType.JOB_STARTED:
            job.title = args[jobmonprot.Request.ARGS_TITLE]
            job.state = Job.State.RUNNING
            job.progress = 0
            job.imageURL = args[jobmonprot.Request.ARGS_IMAGE_URL]
            _logger.info('Started to convert: "%s"' % job.title)
        elif msg_type == NotificationType.JOB_FAILED:
            _logger.warn("Job failed! Exception Args: %s", args)
            job.state = Job.State.FAILED
        elif msg_type == NotificationType.JOB_OUTPUT:
            job.output = job.output if job.output != None else ""
            for line in args[jobmonprot.Request.ARGS_LINES]:
                job.output += line
        elif msg_type == NotificationType.JOB_PROGRESS:
            progress = args[jobmonprot.Request.ARGS_PROGRESS]
            isinstance(progress, int)
            job.progress = progress
        elif msg_type == NotificationType.JOB_CONVERSION_FINISHED:
            _logger.info("Job #{} finished, waiting for file transfer".format(job_ID))
            return
        elif msg_type == NotificationType.JOB_FINISHED:
            job.state = Job.State.FINISHED
            job.progress = 100
            job.archiveCachedUTCDate = dt.utcnow().strftime(Job.DATETIME_FORMAT)

        # find listening clients
        # TODO: cache this...
        listening_client_job_key = webhelpers.REDIS_LISTENING_CLIENT_JOB_KEY_TEMPLATE.format(job_ID)
        all_listening_client_IDs = cls.REDIS_CONNECTION.get(listening_client_job_key)
        if all_listening_client_IDs == None:
            _logger.warn("WTH?! No listening clients stored!")
            if not job.save_to_redis(cls.REDIS_CONNECTION, job_key):
                _logger.info("Unable to update job state!")
            return

        all_listening_client_IDs = ast.literal_eval(all_listening_client_IDs)
        num_clients_of_project = len(all_listening_client_IDs)
        _logger.debug("There %s %d registered client%s." % \
                      ("is" if num_clients_of_project == 1 else "are", \
                       num_clients_of_project, "s" if num_clients_of_project != 1 else ""))

        if msg_type in (NotificationType.JOB_FINISHED, NotificationType.JOB_FAILED):
            # Job completely finished or failed -> remove all listeners from database
            #                                      before updating job state in database
            remove_all_listening_clients_from_job(cls.REDIS_CONNECTION, job_ID)

        # update job state in database
        if not job.save_to_redis(cls.REDIS_CONNECTION, job_key):
            _logger.info("Unable to update job state!")
            return

        currently_listening_client_IDs = filter(lambda client_ID: client_ID in cls.client_ID_open_sockets_map,
                                                all_listening_client_IDs)
        currently_listening_client_sockets = map(lambda client_ID: cls.client_ID_open_sockets_map[client_ID],
                                                 currently_listening_client_IDs)
        _logger.debug("There are %d active clients listening on this job." % len(currently_listening_client_sockets))

        for idx, socket_handlers in enumerate(currently_listening_client_sockets):
            if msg_type == NotificationType.JOB_STARTED:
                message = JobRunningMessage(job_ID, job.title, job.imageURL)
            elif msg_type == NotificationType.JOB_OUTPUT:
                message = JobOutputMessage(job_ID, args[jobmonprot.Request.ARGS_LINES])
            elif msg_type == NotificationType.JOB_PROGRESS:
                message = JobProgressMessage(job_ID, job.progress)
            elif msg_type == NotificationType.JOB_FINISHED:
                client_ID = currently_listening_client_IDs[idx]
                download_url = webhelpers.create_download_url(job_ID, client_ID, job.title)
                message = JobFinishedMessage(job_ID, download_url, None)
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
                return # break out of loop => since there can be no more than 1 clientID per socket


    def send_message(self, message):
        assert isinstance(message, Message)
        _logger.debug("Sending %s %r to %d", message.__class__.__name__, message.as_dict(), id(self))
        try:
            self.write_message(json.dumps(message.as_dict()).decode('unicode-escape').encode('utf8'),
                               binary=False)
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

        ctxt = Context(self, self.__class__.REDIS_CONNECTION, self.application.settings["jobmonitorserver"])
        _logger.info("Executing command %s", command.__class__.__name__)
        reply_message = command.execute(ctxt, args)
        if reply_message is not None:
            _logger.info("Sending reply %s %r to %d", reply_message.__class__.__name__,
                         reply_message.as_dict(), id(self))
            self.send_message(reply_message)

