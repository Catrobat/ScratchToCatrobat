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
#  This script is a simple TCP server appliction based on the Tornado
#  asynchronous networking library, which is licensed under the Apache License,
#  Version 2.0.
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
  TCP server used to communicate between worker jobs and http websocket application.
"""

import logging
import tornado.ioloop
from tornado.tcpserver import TCPServer
from tornado import gen
from jobmonitorserver.jobmonitorprotocol import Request, Reply, TCPConnection, SERVER, CLIENT, NotificationType
from websocketserver.websockethandler import ConverterWebSocketHandler
import json
import time
import datetime
import hashlib
import os
import sys
from scratchtocatrobat.tools import helpers

CATROBAT_FILE_EXT = helpers.config.get("CATROBAT", "file_extension")

_logger = logging.getLogger(__name__)


class TCPConnectionException(Exception):
    def __init__(self, message, context):
        super(TCPConnectionException, self).__init__(message)
        self.context = context

class TCPConnectionHandler(object):
    def __init__(self, server, connection):
        self.server = server
        self.connection = connection
        connection.on_close_callback = self.on_close

    def send_message(self, data):
        self.server.streams[self.connection.stream] = time.time() # last update
        return self.connection.send_message(data)

    def read_message(self):
        self.server.streams[self.connection.stream] = time.time() # last update
        return self.connection.read_message()

    def _extract_data_from_message(self, message):
        message = unicode(message).rstrip()
        _logger.debug("Extracting message: %s" % message)
        return json.loads(message)

    def read_bytes(self, buffer_size):
        stream = self.connection.stream
        self.server.streams[stream] = time.time() # last update
        return stream.read_bytes(buffer_size)

    def on_close(self):
        if self.connection.stream in self.server.streams:
            del self.server.streams[self.connection.stream]
        _logger.debug("Removed stream from stream list!!")

    @gen.coroutine
    def handle_authentication(self):
        data = self._extract_data_from_message((yield self.read_message()))
        if not Request.is_valid(data, Request.Command.AUTH):
            raise TCPConnectionException("Invalid data given!")
        request = Request.request_from_data(data)
        address = self.connection.address
        host = address[0] if isinstance(address, tuple) else address
        allowed_auth_keys = self.server.settings["allowed_auth_keys"]
        allowed_auth_keys_for_host = [auth_key["key"] for auth_key in allowed_auth_keys if auth_key["host"] == host]
        if len(allowed_auth_keys_for_host) == 0:
            _logger.warn("An intruder '%s' might have tried to connect to our server!"
                         % address)
            # TODO: block him...
            # Don't tell the client that this hostname is forbidden
            raise TCPConnectionException("Invalid AUTH_KEY given.")
        if request.args[Request.ARGS_AUTH_KEY] not in allowed_auth_keys_for_host:
            raise TCPConnectionException("Invalid AUTH_KEY given.")

        _logger.info("[%s]: Reply: Authentication successful!" % SERVER)
        yield self.send_message(Reply(result=True, msg="Authentication successful!"))

    @gen.coroutine
    def handle_job_started_notification(self):
        data = self._extract_data_from_message((yield self.read_message()))
        if not Request.is_valid(data, Request.Command.JOB_STARTED_NOTIFICATION):
            raise TCPConnectionException("Invalid data given!")
        request = Request.request_from_data(data)
        _logger.info("[%s]: Received job start notification" % SERVER)
        _logger.info("[%s]: Title of Scratch program: '%s'" % (CLIENT, unicode(request.args[Request.ARGS_TITLE])))

        _logger.debug("[%s]: Reply: Accepted!" % SERVER)
        yield self.send_message(Reply(result=True, msg="ACK"))
        ConverterWebSocketHandler.notify(NotificationType.JOB_STARTED, request.args)

    @gen.coroutine
    def handle_job_output_notification(self, data):
        if not Request.is_valid(data, Request.Command.JOB_OUTPUT_NOTIFICATION):
            raise TCPConnectionException("Invalid data given!")
        request = Request.request_from_data(data)
        _logger.debug("[%s]: Received job output notification" % SERVER)
        for line in request.args[Request.ARGS_LINES]:
            _logger.debug("[%s]: %s" % (CLIENT, line))
#         _logger.debug("[%s]: Reply: Accepted!" % SERVER)
#         yield self.send_message(Reply(result=True, msg="ACK"))
        ConverterWebSocketHandler.notify(NotificationType.JOB_OUTPUT, request.args)

    @gen.coroutine
    def handle_job_progress_notification(self, data):
        if not Request.is_valid(data, Request.Command.JOB_PROGRESS_NOTIFICATION):
            raise TCPConnectionException("Invalid data given!")
        request = Request.request_from_data(data)
        if not isinstance(request.args[Request.ARGS_PROGRESS], int):
            raise TCPConnectionException("Progress parameter must be of type int!")
        _logger.debug("[%s]: Received job progress notification (Progress: %d%%)"
                      % (SERVER, request.args[Request.ARGS_PROGRESS]))

#         _logger.debug("[%s]: Reply: Accepted!" % SERVER)
#         yield self.send_message(Reply(result=True, msg="ACK"))
        ConverterWebSocketHandler.notify(NotificationType.JOB_PROGRESS, request.args)

    @gen.coroutine
    def handle_job_conversion_finished_notification(self, data):
        if data == None or not Request.is_valid(data, Request.Command.JOB_CONVERSION_FINISHED_NOTIFICATION):
            raise TCPConnectionException("Invalid data given!")
        request = Request.request_from_data(data)
        _logger.info("[%s]: Received job finished notification" % SERVER)
        _logger.info("[%s]: %s " % (CLIENT, request.args[Request.ARGS_MSG]))
        exit_code = int(request.args[Request.ARGS_RESULT])
        _logger.info("[%s]: Job finished with exit code: %d" % (SERVER, exit_code))
        if exit_code != 0:
            raise TCPConnectionException("Job failed with exit code: %d" % exit_code, context=request.args)

        _logger.debug("[%s]: Reply: Accepted!" % SERVER)
        yield self.send_message(Reply(result=True, msg="ACK"))
        ConverterWebSocketHandler.notify(NotificationType.JOB_CONVERSION_FINISHED, request.args)

    @gen.coroutine
    def handle_job_finished(self):
        data = self._extract_data_from_message((yield self.read_message()))
        if not Request.is_valid(data, Request.Command.JOB_FINISHED):
            if Request.is_valid(data, Request.Command.JOB_FAILED):
                _logger.warn("[%s] Job failed!" % CLIENT)
                request = Request.request_from_data(data)
                ConverterWebSocketHandler.notify(NotificationType.JOB_FAILED, request.args)
                return
            raise TCPConnectionException("Invalid data given!")
        request = Request.request_from_data(data)
        _logger.info("[%s]: Received file transfer notification" % SERVER)

        job_ID = int(request.args[Request.ARGS_JOB_ID])
        file_name = str(job_ID) + CATROBAT_FILE_EXT
        file_size = int(request.args[Request.ARGS_FILE_SIZE])
        file_hash = request.args[Request.ARGS_FILE_HASH]
        _logger.info("[%s]: Job ID: %d, File size: %d, SHA256: %s"
                     % (CLIENT, job_ID, file_size, file_hash))

        if file_size == 0:
            raise TCPConnectionException("Cannot transfer empty file...", context=request.args)

        _logger.debug("[%s]: Reply: Accepted!" % SERVER)
        yield self.send_message(Reply(result=True, msg="Ready for file transfer!"))

        download_dir = self.server.settings["download_dir"]
        file_path = os.path.join(download_dir, file_name)
        max_input_buffer_size = int(self.server.settings["max_input_buffer_size"])
        with open(file_path, 'wb+', 0) as f:
            if file_size <= max_input_buffer_size:
                f.write((yield self.read_bytes(file_size)))
            else:
                transfered_bytes = 0
                while transfered_bytes < file_size:
                    buffer_size = min((file_size - transfered_bytes), max_input_buffer_size)
                    f.write((yield self.read_bytes(buffer_size)))
                    transfered_bytes += buffer_size
            f.seek(0, 0)
            computed_file_hash = hashlib.sha256(f.read()).hexdigest()
            if computed_file_hash != file_hash:
                raise TCPConnectionException("Given hash value is not equal to computed hash value.", context=request.args)

        _logger.debug("[%s]: Reply: Accepted!" % SERVER)
        _logger.info("OK! Hash is equal to computed hash value. Finished file transfer!")
        yield self.send_message(Reply(result=True, msg="OK! Hash is equal to computed " \
                                      "hash value. Finished file transfer!"))
        ConverterWebSocketHandler.notify(NotificationType.JOB_FINISHED, request.args)

    @gen.coroutine
    def handle_exception(self, exception, msg):
        _logger.error("{}!".format(msg))
        _logger.exception(exception)
        yield self.send_message(Reply(result=False, msg="{}! Closing connection.".format(msg)))
        if isinstance(exception, TCPConnectionException) and exception.context != None:
            args = exception.context
            args["msg"] = msg
            ConverterWebSocketHandler.notify(NotificationType.JOB_FAILED, args)
        else:
            ConverterWebSocketHandler.notify(NotificationType.JOB_FAILED, { "msg": msg })
        self.connection.print_error_and_close_stream()

    @gen.coroutine
    def run(self):
        # (I) Send greeting
        try:
            yield self.send_message(Reply(result=True, msg="Hello Client, please authenticate!"))
        except Exception as e:
            self.handle_exception(e, "Greeting failed")
            return
        except:
            self.handle_exception(sys.exc_info()[0], "Greeting failed")
            return

        # (II) Expecting authentication via AuthKey
        try:
            yield self.handle_authentication()
        except Exception as e:
            self.handle_exception(e, "Authentication failed")
            return
        except:
            self.handle_exception(sys.exc_info()[0], "Authentication failed")
            return

        # (III) Expecting job started notification
        try:
            yield self.handle_job_started_notification()
        except Exception as e:
            self.handle_exception(e, "Processing job started notification failed")
            return
        except:
            self.handle_exception(sys.exc_info()[0], "Processing job started notification failed")
            return

        # (IV) Expecting output and/or progress notifications or job finished notification
        data = None
        try:
            while True:
                data = self._extract_data_from_message((yield self.read_message()))
                if Request.is_valid(data, Request.Command.JOB_CONVERSION_FINISHED_NOTIFICATION):
                    break
                elif Request.is_valid(data, Request.Command.JOB_OUTPUT_NOTIFICATION):
                    yield self.handle_job_output_notification(data)
                elif Request.is_valid(data, Request.Command.JOB_PROGRESS_NOTIFICATION):
                    yield self.handle_job_progress_notification(data)
                else:
                    raise TCPConnectionException("Invalid data given!")
        except Exception as e:
            self.handle_exception(e, "Processing job notification failed")
            return
        except:
            self.handle_exception(sys.exc_info()[0], "Processing job notification failed")
            return

        # (V) Expecting job finished notification
        try:
            yield self.handle_job_conversion_finished_notification(data)
        except Exception as e:
            self.handle_exception(e, "Processing job finished notification failed")
            return
        except:
            self.handle_exception(sys.exc_info()[0], "Processing job finished notification failed")
            return

        # (V) Expecting file transfer
        try:
            yield self.handle_job_finished()
        except Exception as e:
            self.handle_exception(e, "File transfer failed")
            return
        except:
            self.handle_exception(sys.exc_info()[0], "File transfer failed")
            return

        _logger.info("Finished! Closing stream.")
        self.connection.stream.close()

class JobMonitorTCPServer(TCPServer):
    def __init__(self, settings, io_loop=None, ssl_options=None):
        _logger.debug('Job Monitor Server started')
        if not io_loop:
            io_loop = tornado.ioloop.IOLoop.instance()
        self.settings = settings
        self.io_loop = io_loop
        self.streams = {}
        check_zombie_interval = int(settings["check_zombie_interval"])
        self.io_loop.add_timeout(datetime.timedelta(seconds=check_zombie_interval), self.close_streams_after_timeout)
        max_stream_buffer_size = int(settings["max_stream_buffer_size"]) if "max_stream_buffer_size" in settings else None
        read_chunk_size = int(settings["read_chunk_size"]) if "read_chunk_size" in settings else None
        super(JobMonitorTCPServer, self).__init__(io_loop, ssl_options, max_stream_buffer_size, read_chunk_size)

    def stop(self):
        super(JobMonitorTCPServer, self).stop()

    def close_streams_after_timeout(self):
        connection_timeout = float(self.settings["connection_timeout"])
        check_zombie_interval = int(self.settings["check_zombie_interval"])
        _logger.info("Zombie watcher is looking for inactive streams " \
                     "(connection timeout = %d, check interval = %d)", \
                     connection_timeout, check_zombie_interval)
        streams_to_be_removed = []
        for stream, last_update in self.streams.iteritems():
            if stream.closed():
                streams_to_be_removed.append(stream)
            elif (time.time() - last_update) > connection_timeout:
                _logger.warn("Closing inactive stream after %d seconds"
                             % (time.time() - last_update))
                streams_to_be_removed.append(stream)
                stream.close()
        for stream in streams_to_be_removed:
            del self.streams[stream]
        if len(streams_to_be_removed) != 0:
            _logger.info("Zombie watcher automatically closed %d inactive streams."
                         % len(streams_to_be_removed))
        else:
            _logger.debug("No inactive streams found.")
        self.io_loop.add_timeout(datetime.timedelta(seconds=check_zombie_interval), self.close_streams_after_timeout)

    @gen.coroutine
    def handle_stream(self,stream,address):
        self.streams[stream] = time.time()
        conn = TCPConnection(stream, address, CLIENT)
        handler = TCPConnectionHandler(self, conn)
        yield handler.run()
