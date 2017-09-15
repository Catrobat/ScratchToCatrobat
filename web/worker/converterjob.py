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

"""
  This module implements a simple job that is run by a worker process and invokes the
  converter run as child process.
  The Job Handler is used to notify the scheduling-webserver (via a TCP connection).
  The scheduling-webserver maintains all websocket connections to the users and can
  further notify the users about the progress of the currently running job.
"""

import logging
import sys
import ssl
import time
import subprocess
import os
import hashlib
import json
import socket
import urllib2
from worker import jobhandler
from httplib import BadStatusLine
from jobmonitorserver.jobmonitorprotocol import Request, Reply, SERVER, CLIENT
sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "..", "src"))
import helpers as webhelpers
from scratchtocatrobat.tools import helpers
from scratchtocatrobat.scratch import scratchwebapi
from bs4 import BeautifulSoup
from tornado.ioloop import IOLoop
from tornado import gen

# TODO: not best solution! {
reload(sys)
sys.setdefaultencoding('utf-8') #@UndefinedVariable
# }

_logger = logging.getLogger(__name__)

SCRATCH_PROJECT_BASE_URL = helpers.config.get("SCRATCH_API", "project_base_url")
CONVERTER_RUN_SCRIPT_PATH = os.path.join(helpers.APP_PATH, "run")
AUTH_KEY = helpers.config.get("CONVERTER_JOB", "auth_key")
MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = int(helpers.config.get("CONVERTER_JOB", "max_wait_seconds_before_shutdown"))
BUFFER_SIZE = int(helpers.config.get("CONVERTER_JOB", "buffer_size"))
CERTIFICATE_PATH = helpers.config.get("JOBMONITOR_SERVER", "certificate_path")
CATROBAT_FILE_EXT = helpers.config.get("CATROBAT", "file_extension")
LINE_BUFFER_SIZE = 3


class ConverterJobHandler(jobhandler.JobHandler):

    @gen.coroutine
    def run_job(self, args):
        assert isinstance(args["jobID"], int)
        assert isinstance(args["title"], (str, unicode))
        assert isinstance(args["imageURL"], (str, unicode))
        assert isinstance(args["url"], (str, unicode))
        assert isinstance(args["outputDir"], (str, unicode))
        job_ID, title, image_URL = args["jobID"], args["title"], args["imageURL"]

        exec_args = ["/usr/bin/env", "python", CONVERTER_RUN_SCRIPT_PATH,
                     args["url"], args["outputDir"], str(args["jobID"]), "--web-mode"]
        process = subprocess.Popen(exec_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        yield self.send_job_started_notification(job_ID, title, image_URL)

        start_progr_indicator = helpers.ProgressBar.START_PROGRESS_INDICATOR
        end_progr_indicator = helpers.ProgressBar.END_PROGRESS_INDICATOR
        line_buffer = []
        old_progress = 0
        while True:
            line = process.stdout.readline()
            if line == '': break
            line = line.rstrip()

            # case: progress update
            if line.startswith(start_progr_indicator) and line.endswith(end_progr_indicator):
                progress = line.split(start_progr_indicator)[1].split(end_progr_indicator)[0]
                if not helpers.isfloat(progress):
                    _logger.warn("[%s]: Ignoring line! Parsed progress is no valid float: '%s'"
                                 % (CLIENT, progress))
                    continue

                progress = int(float(progress))
                progress_difference = progress - old_progress
                old_progress = progress
                if progress_difference > 0:
                    _logger.debug("[{}]: {}".format(CLIENT, progress))
                    yield self.send_job_progress_notification(job_ID, progress)
                continue

            # case: console output
            _logger.debug("[%s]: %s" % (CLIENT, line))
            line_buffer += [line]
            if self._verbose and len(line_buffer) >= LINE_BUFFER_SIZE:
                yield self.send_job_output_notification(job_ID, line_buffer)
                line_buffer = []

        if self._verbose and len(line_buffer):
            yield self.send_job_output_notification(job_ID, line_buffer)

        exit_code = process.wait() # XXX: work around this when experiencing errors...
        _logger.info("[%s]: Exit code is: %d" % (CLIENT, exit_code))

        # NOTE: exit-code is evaluated by TCP server
        yield self.send_job_conversion_finished_notification(job_ID, exit_code)

    @gen.coroutine
    def post_processing(self, args):
        file_path = os.path.join(args["outputDir"], str(args["jobID"]) + CATROBAT_FILE_EXT)
        if not os.path.isfile(file_path):
            yield self._connection.send_message(Request(Request.Command.JOB_FAILED, {
                Request.ARGS_JOB_ID: args["jobID"],
                Request.ARGS_MSG: "Cannot transfer file! File does not exist!"
            }))
            return

        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as fp:
            file_hash = hashlib.sha256(fp.read()).hexdigest()
            args = {
                Request.ARGS_JOB_ID: args["jobID"],
                Request.ARGS_FILE_SIZE: file_size,
                Request.ARGS_FILE_HASH: file_hash
            }
            yield self._connection.send_message(Request(Request.Command.JOB_FINISHED, args))

            # File transfer ready (reply)
            data = json.loads((yield self._connection.read_message()).rstrip())
            if not Reply.is_valid(data):
                raise Exception("Invalid reply!")
            reply = Reply(data[Reply.KEY_RESULT], data[Reply.KEY_MSG])
            if not reply.result:
                _logger.error("[%s]: %s" % (SERVER, reply.msg))
                raise Exception("File transfer failed!")
            _logger.info('[%s]: "%s"' % (SERVER, reply.msg))

            fp.seek(0, 0)
            _logger.info("[%s]: Sending..." % CLIENT)
            byte_buffer = fp.read(BUFFER_SIZE)
            while byte_buffer:
                yield self._connection.send_message(byte_buffer, logging_enabled=False)
                byte_buffer = fp.read(BUFFER_SIZE)
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

def convert_scratch_project(job_ID, host, port, verbose):
    logging.basicConfig(
        filename=None,
        level=logging.DEBUG,
        format='%(asctime)s: %(levelname)7s: [%(name)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

#     job = get_current_job()
#     job.meta['handled_by'] = socket.gethostname()
#     job.save()

    # validate URL
    if job_ID == None or not isinstance(job_ID, int):
        _logger.error("No or invalid Scratch project ID given: {}".format(job_ID))
        return

    if not os.path.isfile(CERTIFICATE_PATH):
        _logger.error("Cannot find server certificate: %s", CERTIFICATE_PATH)
        return

    retries = int(helpers.config.get("SCRATCH_API", "http_retries"))
    timeout_in_secs = int(helpers.config.get("SCRATCH_API", "http_timeout")) / 1000
    backoff = int(helpers.config.get("SCRATCH_API", "http_backoff"))
    delay = int(helpers.config.get("SCRATCH_API", "http_delay"))
    user_agent = helpers.config.get("SCRATCH_API", "user_agent")

    # preprocessing: fetch project title and project image URL via web API
    def retry_hook(exc, tries, delay):
        _logger.warning("  Exception: {}\nRetrying after {}:'{}' in {} secs (remaining trys: {})" \
                        .format(sys.exc_info()[0], type(exc).__name__, exc, delay, tries))

    @helpers.retry((urllib2.URLError, socket.timeout, IOError, BadStatusLine), delay=delay,
                   backoff=backoff, tries=retries, hook=retry_hook)
    def read_content_of_url(url):
        _logger.info("Fetching project title from: {}".format(scratch_project_url))
        req = urllib2.Request(url, headers={ "User-Agent": user_agent })
        return urllib2.urlopen(req, timeout=timeout_in_secs).read()

    title = None
    image_URL = None
    scratch_project_url = "%s%d" % (SCRATCH_PROJECT_BASE_URL, job_ID)
    try:
        html_content = read_content_of_url(scratch_project_url)
        if html_content == None or not isinstance(html_content, str):
            raise Warning("Unable to set title of project from the project's " \
                          "website! Reason: Invalid or empty html content!")

        document = webhelpers.ResponseBeautifulSoupDocumentWrapper(BeautifulSoup(html_content.decode('utf-8', 'ignore'), b'html5lib'))
        title = scratchwebapi.extract_project_title_from_document(document)
        image_URL = scratchwebapi.extract_project_image_url_from_document(document)
        if title == None:
            raise Warning("Unable to set title of project from the project's website!" \
                          " Reason: Cannot parse title from returned html content!")
        if image_URL == None:
            raise Warning("Unable to extract image url of project from the project's website!" \
                          " Reason: Cannot parse image url from returned html content!")
    except:
        # log error and continue without updating title and/or image URL!
        _logger.error("Unexpected error for URL: {}, {}".format(scratch_project_url, \
                                                                sys.exc_info()[0]))

    _logger.info("Project title is: {}".format(title))

    args = {
        "url": scratch_project_url,
        "jobID": job_ID,
        "title": title,
        "imageURL": image_URL,
        "outputDir": helpers.config.get("PATHS", "web_output")
    }

    # set up signal handler
    #signal.signal(signal.SIGTERM, sig_handler)
    #signal.signal(signal.SIGINT, sig_handler)

    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2) #@UndefinedVariable
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    # check only hostnames for non-local servers
    ssl_ctx.check_hostname = (host != "localhost")
    ssl_ctx.load_verify_locations(cafile=CERTIFICATE_PATH)

    handler = ConverterJobHandler(host, port, verbose, AUTH_KEY, ssl_options=ssl_ctx)
    handler.run(args)
    IOLoop.instance().start()

# def sig_handler(sig, frame):
#     _logger.warning('Caught signal: %s', sig)
#     IOLoop.instance().add_callback_from_signal(shutdown)
