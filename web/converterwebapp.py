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
#
#  ---------------------------------------------------------------------------------------
#  NOTE:
#  ---------------------------------------------------------------------------------------
#  This module is a simple websocket application based on the Tornado
#  web framework and asynchronous networking library, which is
#  licensed under the Apache License, Version 2.0.
#  For more information about the Apache License please visit:
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  For scheduling purposes the rq library (based on Redis) is used.
#  The rq library is licensed under the BSD License:
#
#    https://raw.github.com/nvie/rq/master/LICENSE
#

"""
  Simple websocket application for handling conversion requests.
"""

import logging
import tornado.escape
import tornado.web
import tornado.websocket
import os.path
import redis
from command import get_command, InvalidCommand, Job
import jobmonitorprotocol as jobmonprot
from tornado.web import HTTPError
import ast
import sys

sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "..", "src"))
from scratchtocatrobat.tools import helpers

_logger = logging.getLogger(__name__)

CATROBAT_FILE_EXT = helpers.config.get("CATROBAT", "file_extension")
# TODO: check if redis is available => error!
_redis_conn = redis.Redis() #'127.0.0.1', 6789) #, password='secret')

class Context(object):
    def __init__(self, handler, redis_connection, jobmonitorserver_settings):
        self.handler = handler
        self.redis_connection = redis_connection
        self.jobmonitorserver_settings = jobmonitorserver_settings

class _JsonKeys(object):
    class Request(object):
        CMD = "cmd"
        ARGS = "args"

        ARGS_CLIENT_ID = "clientID"
        ARGS_URL = "url"
        allowed_arg_keys = [ARGS_CLIENT_ID, ARGS_URL]

        @classmethod
        def is_valid(cls, data):
            return (data is not None) and (cls.CMD in data) and (cls.ARGS in data)

        @classmethod
        def extract_allowed_args(cls, args):
            filtered_args = {}
            for key in cls.allowed_arg_keys:
                if key in args:
                    filtered_args[key] = args[key]
            return filtered_args

    class Reply(object):
        #TYPE = "type"
        STATUS = "status"
        DATA = "data"

class NotificationType():
    JOB_STARTED = 0
    JOB_PROGRESS = 1
    JOB_FINISHED = 2
    FILE_TRANSFER_FINISHED = 3
    JOB_FAILED = 4

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
    def notify(cls, type, args):
        # jobID is scratch project ID in this case
        scratch_project_ID = args[jobmonprot.Request.ARGS_JOB_ID]
        REDIS_CLIENT_PROJECT_KEY = "clientsOfProject#{}".format(scratch_project_ID)
        REDIS_PROJECT_KEY = "project#{}".format(scratch_project_ID)

        REDIS_PROJECT_KEY = "project#{}".format(scratch_project_ID)
        job = Job.from_redis(_redis_conn, REDIS_PROJECT_KEY)
        if job == None:
            _logger.error("Cannot find job #{}".format(scratch_project_ID))
            return
        if type == NotificationType.JOB_STARTED:
            job.status = Job.Status.RUNNING
        elif type == NotificationType.JOB_FAILED:
            _logger.info("Job failed!")
            job.status = Job.Status.FAILED
        elif type == NotificationType.FILE_TRANSFER_FINISHED:
            job.status = Job.Status.FINISHED
        elif type == NotificationType.JOB_FINISHED:
            _logger.info("Job #{} finished, waiting for file transfer".format(scratch_project_ID))

        if not job.save_to_redis(_redis_conn, REDIS_PROJECT_KEY):
            _logger.info("Unable to update job status!")
            return

        # find listening clients
        # TODO: cache this...
        clients_of_project = _redis_conn.get(REDIS_CLIENT_PROJECT_KEY)
        if clients_of_project == None:
            _logger.warn("WTH?! No listening clients stored!")
            return
        clients_of_project = ast.literal_eval(clients_of_project)
        _logger.debug("There are %d registered clients." % len(clients_of_project))
        listening_clients = [cls.client_ID_open_sockets_map[int(client_ID)] for client_ID in clients_of_project if int(client_ID) in cls.client_ID_open_sockets_map]
        _logger.info("There are %d active clients listening on this job." % len(listening_clients))

        for socket_handlers in listening_clients:
            #if type == NotificationType.JOB_STARTED:
            #    message = { _JsonKeys.Reply.STATUS: True, _JsonKeys.Reply.DATA: { "msg": "JOB STARTED!" } }
            #elif type == NotificationType.JOB_PROGRESS:
            #    message = { _JsonKeys.Reply.STATUS: True, _JsonKeys.Reply.DATA: { "msg": args[jobmonprot.Request.ARGS_MSG] } }
            #elif type == NotificationType.JOB_FINISHED:
            #    message = { _JsonKeys.Reply.STATUS: True, _JsonKeys.Reply.DATA: { "msg": args[jobmonprot.Request.ARGS_MSG] } }
            if type == NotificationType.FILE_TRANSFER_FINISHED:
                # send download link!
                download_url = "/download?id=" + scratch_project_ID
                message = { _JsonKeys.Reply.STATUS: True, _JsonKeys.Reply.DATA: { "msg": "File transfer successful!", "url": download_url } }
            elif type == NotificationType.JOB_FAILED:
                message = { _JsonKeys.Reply.STATUS: True, _JsonKeys.Reply.DATA: { "msg": "Job failed!" } }
            else:
                print(">>> UNKNOWN MESSAGE")
                return
            for handler in socket_handlers:
                handler.send_message(message)

    def on_close(self):
        cls = self.__class__
        for (client_ID, open_sockets) in cls.client_ID_open_sockets_map.iteritems():
            if self in open_sockets:
                open_sockets.remove(self)
                if len(open_sockets) == 0:
                    del cls.client_ID_open_sockets_map[client_ID]
                else:
                    cls.client_ID_open_sockets_map[client_ID] = open_sockets
                return # skip loop => maximal 1 socket/clientID possible

    def send_message(self, data):
        _logger.debug("Sending message %r to %d", data, id(self))
        try:
            self.write_message(tornado.escape.json_encode(data))
        except:
            _logger.error("Error sending message", exc_info=True)

    def on_message(self, message):
        _logger.debug("Received message %r", message)
        data = tornado.escape.json_decode(message)
        args = {}
        if _JsonKeys.Request.is_valid(data):
            command = get_command(data[_JsonKeys.Request.CMD])
            args = _JsonKeys.Request.extract_allowed_args(data[_JsonKeys.Request.ARGS])
        else:
            command = InvalidCommand()
        # TODO: sanity check... when client ID is given => check if it belongs to socket handler!
        redis_conn = _redis_conn
        ctxt = Context(self, redis_conn, self.application.settings["jobmonitorserver"])
        result = command.execute(ctxt, args)
        message = { _JsonKeys.Reply.STATUS: result.status, _JsonKeys.Reply.DATA: result.data }
        self.send_message(message)

class _MainHandler(tornado.web.RequestHandler):
    app_data = {}
    def get(self):
        self.render("index.html", data=_MainHandler.app_data)

class _DownloadHandler(tornado.web.RequestHandler):
    def get(self):
        scratch_project_id_string = self.get_query_argument("id", default=None)
        if scratch_project_id_string == None or not scratch_project_id_string.isdigit():
            raise HTTPError(404)
        download_dir = self.application.settings["jobmonitorserver"]["download_dir"]
        file_dir = download_dir
        file_name = scratch_project_id_string + CATROBAT_FILE_EXT
        file_path = "%s/%s" % (file_dir, file_name)
        if not file_name or not os.path.exists(file_path):
            raise HTTPError(404)
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s' % file_name)
        with open(file_path, "rb") as f:
            try:
                while True:
                    _buffer = f.read(4096)
                    if _buffer:
                        self.write(_buffer)
                    else:
                        f.close()
                        self.finish()
                        return
            except:
                raise HTTPError(404)
        raise HTTPError(500)

class ConverterWebApp(tornado.web.Application):
    def __init__(self, **settings):
        self.settings = settings
        handlers = [
            (r"/", _MainHandler),
            (r"/download", _DownloadHandler),
            (r"/convertersocket", ConverterWebSocketHandler),
        ]
        tornado.web.Application.__init__(self, handlers, **settings)
