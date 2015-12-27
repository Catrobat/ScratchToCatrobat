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
from command import get_command, InvalidCommand

_logger = logging.getLogger(__name__)

class _JsonKeys(object):
    class Request(object):
        CMD = "cmd"
        ARGS = "args"
        allowed_arg_keys = ["url"]

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

class _ConverterWebSocketHandler(tornado.websocket.WebSocketHandler):
    handlers_of_open_sockets = set()

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        self.__class__.handlers_of_open_sockets.add(self)

    def on_close(self):
        self.__class__.handlers_of_open_sockets.remove(self)

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

        args["host"] = "localhost"
        args["port"] = 20000
        result = command.execute(args)
        message = { _JsonKeys.Reply.TYPE: result.type, _JsonKeys.Reply.MSG: result.message }
        self.send_message(message)

class _MainHandler(tornado.web.RequestHandler):
    app_data = {}
    def get(self):
        self.render("index.html", data=_MainHandler.app_data)

class ConverterWebApp(tornado.web.Application):
    def __init__(self, **settings):
        handlers = [
            (r"/", _MainHandler),
            (r"/convertersocket", _ConverterWebSocketHandler),
        ]
        tornado.web.Application.__init__(self, handlers, **settings)
