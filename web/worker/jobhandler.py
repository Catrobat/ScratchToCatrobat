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

import tornado.tcpclient
from tornado import gen
from jobmonitorserver.jobmonitorprotocol import Request, Reply, TCPConnection, SERVER, CLIENT
import logging
import json

_logger = logging.getLogger(__name__)


class JobTCPClient(tornado.tcpclient.TCPClient):
    pass

class JobHandler(object):
    def __init__(self, host, port, verbose, auth_key, ssl_options):
        self._host = host
        self._port = port
        self._verbose = verbose
        self._auth_key = auth_key
        self._ssl_options = ssl_options
        self._connection = None
        self._job_client = JobTCPClient()

    @gen.coroutine
    def connect(self):
        _logger.debug('[%s]: Opening new connection to "%s"' % (CLIENT, str(self._host)))
        stream = yield self._job_client.connect(self._host, self._port, ssl_options=self._ssl_options)
        self._connection = TCPConnection(stream, self._host, SERVER, on_close_callback=self.shutdown)
        _logger.info('[%s]: Connected to "%s"' % (CLIENT, str(self._host)))

    @gen.coroutine
    def receive_greeting(self):
        data = json.loads((yield self._connection.read_message()).rstrip())
        if not Reply.is_valid(data):
            raise Exception("Invalid reply!")
        reply = Reply(data[Reply.KEY_RESULT], data[Reply.KEY_MSG])
        if not reply.result:
            _logger.error("[%s]: %s" % (SERVER, reply.msg))
            raise Exception("Greeting failed!")
        _logger.info('[%s]: "%s"' % (SERVER, reply.msg))

    @gen.coroutine
    def authenticate(self):
        _logger.debug('[%s]: Start authentication' % CLIENT)
        request = Request(Request.Command.AUTH, { Request.ARGS_AUTH_KEY: self._auth_key})
        yield self._connection.send_message(request, logging_enabled=False) # do not log key!

        data = json.loads((yield self._connection.read_message()).rstrip())
        if not Reply.is_valid(data):
            raise Exception("Invalid reply!")
        reply = Reply(data[Reply.KEY_RESULT], data[Reply.KEY_MSG])
        if not reply.result:
            _logger.error("[%s]: %s" % (SERVER, reply.msg))
            raise Exception("Authentication failed!")
        _logger.info('[%s]: "%s"' % (SERVER, reply.msg))

    @gen.coroutine
    def send_job_started_notification(self, job_ID, title, image_URL):
        _logger.debug('[%s]: Sending job started notification' % CLIENT)
        args = {
            Request.ARGS_JOB_ID: job_ID,
            Request.ARGS_IMAGE_URL: image_URL,
            Request.ARGS_TITLE: title,
            Request.ARGS_MSG: "Job started"
        }
        request = Request(Request.Command.JOB_STARTED_NOTIFICATION, args)
        yield self._connection.send_message(request)
        # Job started (reply)
        data = json.loads((yield self._connection.read_message()).rstrip())
        if not Reply.is_valid(data):
            raise Exception("Invalid reply!")
        reply = Reply(data[Reply.KEY_RESULT], data[Reply.KEY_MSG])
        if not reply.result:
            _logger.error("[%s]: %s" % (SERVER, reply.msg))
            raise Exception("Job started notification failed!")
        _logger.info('[%s]: "%s"' % (SERVER, reply.msg))

    @gen.coroutine
    def send_job_progress_notification(self, job_ID, progress):
        # Job progress (request)
        if not isinstance(progress, int):
            _logger.warn("[{}]: Cannot send progress notification! Given progress is "\
                         "no valid int: '{}'".format(CLIENT, progress))
            return

        _logger.debug('[%s]: (%d%%) Sending job progress notification' % (CLIENT, progress))
        args = { Request.ARGS_JOB_ID: job_ID, Request.ARGS_PROGRESS: progress }
        yield self._connection.send_message(Request(Request.Command.JOB_PROGRESS_NOTIFICATION, args))

#         # Job progress (reply)
#         data = json.loads((yield self._connection.read_message()).rstrip())
#         if not Reply.is_valid(data):
#             raise Exception("Invalid reply!")
#         reply = Reply(data[Reply.KEY_RESULT], data[Reply.KEY_MSG])
#         if not reply.result:
#             _logger.error("[%s]: %s" % (SERVER, reply.msg))
#             raise Exception("Job progress notification failed!")
#         _logger.info('[%s]: "%s"' % (SERVER, reply.msg))

    @gen.coroutine
    def send_job_output_notification(self, job_ID, messages):
        # Job output (request)
        assert isinstance(messages, list)
        messages = map(lambda message: message.replace('"', ''), messages)
        _logger.debug('[%s]: Sending job output notification: %s' % (CLIENT, "\n".join(messages)))
        args = { Request.ARGS_JOB_ID: job_ID, Request.ARGS_LINES: messages }
        yield self._connection.send_message(Request(Request.Command.JOB_OUTPUT_NOTIFICATION, args))

#         # Job output (reply)
#         data = json.loads((yield self._connection.read_message()).rstrip())
#         if not Reply.is_valid(data):
#             raise Exception("Invalid reply!")
#         reply = Reply(data[Reply.KEY_RESULT], data[Reply.KEY_MSG])
#         if not reply.result:
#             _logger.error("[%s]: %s" % (SERVER, reply.msg))
#             raise Exception("Job output notification failed!")
#         _logger.info('[%s]: "%s"' % (SERVER, reply.msg))

    @gen.coroutine
    def send_job_conversion_finished_notification(self, job_ID, exit_code):
        # Job finished (request)
        _logger.debug('[%s]: Sending job finished notification' % CLIENT)
        args = { Request.ARGS_JOB_ID: job_ID, Request.ARGS_RESULT: exit_code, Request.ARGS_MSG: "Job finished" }
        yield self._connection.send_message(Request(Request.Command.JOB_CONVERSION_FINISHED_NOTIFICATION, args))

        # Job finished (reply)
        data = json.loads((yield self._connection.read_message()).rstrip())
        if not Reply.is_valid(data):
            raise Exception("Invalid reply!")
        reply = Reply(data[Reply.KEY_RESULT], data[Reply.KEY_MSG])
        if not reply.result:
            _logger.error("[%s]: %s" % (SERVER, reply.msg))
            raise Exception("Job finished notification failed!")
        _logger.info('[%s]: "%s"' % (SERVER, reply.msg))

    @gen.coroutine
    def pre_processing(self, args):
        pass # optional => you may implement this in your subclass

    @gen.coroutine
    def run_job(self, args):
        raise Exception("FAILED!!! You MUST implement this method in the subclass.")

    @gen.coroutine
    def post_processing(self, args):
        pass # optional => you may implement this in your subclass

    def shutdown(self):
        pass # optional => you may implement this in your subclass

    @gen.coroutine
    def handle_exception(self, msg):
        _logger.exception("{}!".format(msg))
        self._connection.print_error_and_close_stream()

    @gen.coroutine
    def run(self, args):
        # (I) Connect to server
        try:
            yield self.connect()
        except:
            self.handle_exception("Cannot connect to server")
            return

        # (II) Receive greeting
        try:
            yield self.receive_greeting()
        except:
            self.handle_exception("Unable to receive greeting")
            return

        # (III) Authentication
        try:
            yield self.authenticate()
        except:
            self.handle_exception("Authentication failed")
            return

        # (IV) Pre processing
        try:
            yield self.pre_processing(args)
        except:
            self.handle_exception("Pre processing failed...")
            return

        # (V) Run job
        try:
            yield self.run_job(args)
        except:
            self.handle_exception("Unable to run job")
            return

        # (VI) Post processing (e.g. file transfer, send email, ...)
        try:
            yield self.post_processing(args)
        except:
            self.handle_exception("Post processing failed...")
            return

        # (VII) Shutdown Job Handler
        self.shutdown()
