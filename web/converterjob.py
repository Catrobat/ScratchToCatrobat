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

"""
  This module implements a simple job that is run by a worker process and calls the
  converter in a child process.
  Here, the Job Handler is used to notify the scheduling webserver (via a TCP connection).
  The scheduling webserver maintains all websocket connections to the users and can
  further notify the users about the progress of the currently running jobs.
"""

import logging
import sys
import signal
import ssl
import time
import subprocess
import os
import hashlib
import json
import socket
import urllib2
from httplib import BadStatusLine

from tornado.ioloop import IOLoop
from tornado import gen
import jobhandler
from jobmonitorprotocol import Request, Reply, SERVER, CLIENT

sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "..", "src"))
from scratchtocatrobat.tools import helpers

_logger = logging.getLogger(__name__)

SCRATCH_PROJECT_BASE_URL = helpers.config.get("SCRATCH_API", "project_base_url")
CONVERTER_RUN_SCRIPT_PATH = os.path.join(helpers.APP_PATH, "run")
AUTH_KEY = helpers.config.get("CONVERTER_JOB", "auth_key")
MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = int(helpers.config.get("CONVERTER_JOB", "max_wait_seconds_before_shutdown"))
BUFFER_SIZE = int(helpers.config.get("CONVERTER_JOB", "buffer_size"))
CERTIFICATE_PATH = helpers.config.get("JOBMONITOR_SERVER", "certificate_path")
CATROBAT_FILE_EXT = helpers.config.get("CATROBAT", "file_extension")
PROJECT_INFO_URL_TEMPLATE = helpers.config.get("SCRATCH_API", "project_info_url_template")

class ConverterJobHandler(jobhandler.JobHandler):

    @gen.coroutine
    def run_job(self, args):
        exec_args = ["/usr/bin/env", "python", CONVERTER_RUN_SCRIPT_PATH,
                     args["url"], args["outputDir"], args["archiveName"], "--web-mode"]
        process = subprocess.Popen(exec_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        job_ID = str(args["projectID"])
        title = args["title"] if isinstance(args["title"], (str, unicode)) else str(args["title"])
        yield self.send_job_started_notification(job_ID, title)

        start_progr_indicator = helpers.ProgressBar.START_PROGRESS_INDICATOR
        end_progr_indicator = helpers.ProgressBar.END_PROGRESS_INDICATOR
        while True:
            line = process.stdout.readline()
            if line == '': break
            line = line.rstrip()

            # case: check if progress update
            if line.startswith(start_progr_indicator) and line.endswith(end_progr_indicator):
                progress = line.split(start_progr_indicator)[1].split(end_progr_indicator)[0]
                if not helpers.isfloat(progress):
                    _logger.warn("[%s]: Ignoring line! Parsed progress is no valid float: '%s'" % (CLIENT, progress))
                    continue
                progress = float(progress)
                yield self.send_job_progress_notification(job_ID, progress)
                _logger.debug("[%s]: %d" % (CLIENT, progress))
                continue

            # case: console output
            _logger.debug("[%s]: %s" % (CLIENT, line))
            yield self.send_job_output_notification(job_ID, line)

        exit_code = process.wait() # XXX: work around this when experiencing errors...
        _logger.info("[%s]: Exit code is: %d" % (CLIENT, exit_code))

        # NOTE: exit code is evaluated on the server
        yield self.send_job_finished_notification(job_ID, exit_code)

    @gen.coroutine
    def post_processing(self, args):
        file_path = os.path.join(args["outputDir"], args["archiveName"] + CATROBAT_FILE_EXT)
        if not os.path.isfile(file_path):
            yield self._connection.send_message(Request(Request.Command.JOB_FAILED, {
                Request.ARGS_JOB_ID: str(args["projectID"]),
                Request.ARGS_MSG: "Cannot transfer file! File does not exist!"
            }))
            return
        file_size = os.path.getsize(file_path)

        with open(file_path, 'rb') as file:
            file_hash = hashlib.sha256(file.read()).hexdigest()
            args = {
                Request.ARGS_JOB_ID: str(args["projectID"]),
                Request.ARGS_FILE_NAME: str(args["projectID"]) + CATROBAT_FILE_EXT,
                Request.ARGS_FILE_SIZE: file_size,
                Request.ARGS_FILE_HASH: file_hash
            }
            yield self._connection.send_message(Request(Request.Command.FILE_TRANSFER, args))

            # File transfer ready (reply)
            data = json.loads((yield self._connection.read_message()).rstrip())
            if not Reply.is_valid(data):
                raise Exception("Invalid reply!")
            reply = Reply(data[Reply.KEY_RESULT], data[Reply.KEY_MSG])
            if not reply.result:
                _logger.error("[%s]: %s" % (SERVER, reply.msg))
                raise Exception("File transfer failed!")
            _logger.info('[%s]: "%s"' % (SERVER, reply.msg))

            file.seek(0, 0)
            _logger.info("[%s]: Sending..." % CLIENT)
            buffer = file.read(BUFFER_SIZE)
            while buffer:
                yield self._connection.send_message(buffer, logging_enabled=False)
                buffer = file.read(BUFFER_SIZE)
            _logger.info("[%s]: Done Sending..." % CLIENT)

            # File transfer finished (reply)
            data = json.loads((yield self._connection.read_message()).rstrip())
            if not Reply.is_valid(data):
                raise Exception("Invalid reply!")
            reply = Reply(data[Reply.KEY_RESULT], data[Reply.KEY_MSG])
            if not reply.result:
                _logger.error("[%s]: %s" % (SERVER, reply.msg))
                raise Exception("File transfer failed!")
            _logger.info('[%s]: "%s"' % (SERVER, reply.msg))

    def shutdown(self):
        _logger.info('Will shutdown in %s seconds ...', MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
        io_loop = IOLoop.instance()
        deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN

        def stop_io_loop():
            now = time.time()
            if now < deadline and (io_loop._callbacks or io_loop._timeouts):
                io_loop.add_timeout(now + 1, stop_io_loop)
            else:
                io_loop.stop()
                _logger.info('Shutdown')
        stop_io_loop()

def convert_scratch_project(scratch_project_ID, host, port):
    logging.basicConfig(
        filename=None,
        level=logging.DEBUG,
        format='%(asctime)s: %(levelname)7s: [%(name)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # validate URL
    if scratch_project_ID == None or not isinstance(scratch_project_ID, int):
        _logger.error("No or invalid Scratch project ID given: {}".format(scratch_project_ID))
        return

    if not os.path.isfile(CERTIFICATE_PATH):
        _logger.error("Cannot find server certificate: %s", CERTIFICATE_PATH)
        return

    # preprocessing: get project title via web API
    retries = int(helpers.config.get("SCRATCH_API", "http_retries"))
    backoff = int(helpers.config.get("SCRATCH_API", "http_backoff"))
    delay = int(helpers.config.get("SCRATCH_API", "http_delay"))
    timeout = int(helpers.config.get("SCRATCH_API", "http_timeout")) / 1000
    url = PROJECT_INFO_URL_TEMPLATE.format(scratch_project_ID)

    def retry_hook(exc, tries, delay):
        _logger.warning("  Exception: {}\nRetrying after {}:'{}' in {} secs (remaining trys: {})".format(sys.exc_info()[0], type(exc).__name__, exc, delay, tries))

    @helpers.retry((urllib2.URLError, socket.timeout, IOError, BadStatusLine), delay=delay, backoff=backoff, tries=retries, hook=retry_hook)
    def request():
        return urllib2.urlopen(url, timeout=timeout).read()

    title = None
    try:
        response = request()
        info = json.loads(response)
        title = info["title"]
    except:
        pass # do not update title...

    # reconstruct URL
    scratch_project_url = "%s%d" % (SCRATCH_PROJECT_BASE_URL, scratch_project_ID)
    args = {
        "url": scratch_project_url,
        "projectID": scratch_project_ID,
        "title": title,
        "outputDir": helpers.config.get("PATHS", "web_output"),
        "archiveName": str(scratch_project_ID)
    }

    # set up signal handler
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    # check only hostnames of non-local servers
    ssl_ctx.check_hostname = (host != "localhost")
    ssl_ctx.load_verify_locations(cafile=CERTIFICATE_PATH)

    handler = ConverterJobHandler(host, port, AUTH_KEY, ssl_options=ssl_ctx)
    handler.run(args)
    IOLoop.instance().start()

def sig_handler(sig, frame):
    _logger.warning('Caught signal: %s', sig)
    IOLoop.instance().add_callback_from_signal(shutdown)
