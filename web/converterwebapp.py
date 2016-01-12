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
        TYPE = "type"
        MSG = "msg"

class ConverterWebSocketHandler(tornado.websocket.WebSocketHandler):

    client_ID_open_sockets_map = {}

    def get_compression_options(self):
        return {} # Non-None enables compression with default options.

    def open(self):
        self.__class__.handlers_of_open_sockets.add(self)

    def set_client_ID(self, client_ID):
        cls = self.__class__
        if client_ID not in cls.client_ID_open_sockets_map:
            cls.client_ID_open_sockets_map[client_ID] = []
        cls.client_ID_open_sockets_map[client_ID].append(self)

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
        file_name = self.get_query_argument("file", default=None)
        if file_name == None:
            raise HTTPError(404)
        download_dir = self.application.settings["jobmonitorserver"]["download_dir"]
        #------------------------
        # FIXME: VALIDATE if file_name...
        #------------------------
        _file_dir = download_dir
        _file_path = "%s/%s" % (_file_dir, file_name)
        if not file_name or not os.path.exists(_file_path):
            raise HTTPError(404)
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s' % file_name)
        with open(_file_path, "rb") as f:
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
        handlers = [
            (r"/", _MainHandler),
            (r"/downloads", _DownloadHandler),
            (r"/convertersocket", ConverterWebSocketHandler),
        ]
        tornado.web.Application.__init__(self, handlers, **settings)
