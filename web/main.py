#!/usr/bin/env python
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
#  This module sets up a TCP and HTTP server based on the Tornado web framework and
#  asynchronous networking library, which is licensed under the
#  Apache License, Version 2.0.
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
import tornado.ioloop
from tornado.options import define, options #@UnusedImport
import converterhttpserver
import converterwebapp
from jobmonitorserver import jobmonitortcpserver
import sys
import os.path
import signal
import time
import ssl
sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "..", "src"))
from scratchtocatrobat.tools import helpers

# TODO: not best solution! {
reload(sys)
sys.setdefaultencoding('utf-8') #@UndefinedVariable
# }

MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = int(helpers.config.get("WEBSERVER", "max_wait_seconds_before_shutdown"))
CERTIFICATE_PATH = helpers.config.get("JOBMONITOR_SERVER", "certificate_path")
CERTIFICATE_KEY_PATH = helpers.config.get("JOBMONITOR_SERVER", "certificate_key_path")
WEBSERVER_PORT = helpers.config.get("WEBSERVER", "port")
WEBSERVER_DEBUG_MODE_ENABLED = str(helpers.config.get("WEBSERVER", "debug")) in {"True", "1"}
WEBSERVER_COOKIE_SECRET = str(helpers.config.get("WEBSERVER", "cookie_secret"))
WEBSERVER_XSRF_COOKIES_ENABLED = str(helpers.config.get("WEBSERVER", "xsrf_cookies")) in {"True", "1"}
JOBMONITORSERVER_PORT = helpers.config.get("JOBMONITOR_SERVER", "port")
_logger = logging.getLogger(__name__)

def sig_handler(sig, frame):
    _logger.warning('Caught signal: %s', sig)
    tornado.ioloop.IOLoop.instance().add_callback_from_signal(shutdown)

def shutdown():
    _logger.info('Stopping TCP server')
    tcp_server.stop()
    _logger.info('Stopping HTTP server')
    web_server.stop()
    _logger.info('Will shutdown in %s seconds ...', MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
    io_loop = tornado.ioloop.IOLoop.instance()
    deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN

    def stop_io_loop():
        global tcp_io_loop
        now = time.time()
        if now < deadline and (io_loop._callbacks or io_loop._timeouts):
            io_loop.add_timeout(now + 1, stop_io_loop)
        else:
            io_loop.stop()
            tcp_io_loop.stop()
            _logger.info('Shutdown IO Loops')

    stop_io_loop()

def main():
    logging.basicConfig(
        filename=None,
        level=logging.DEBUG,
        format='%(asctime)s: %(levelname)7s: [%(name)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    if not os.path.isfile(CERTIFICATE_PATH):
        _logger.error("Cannot find server certificate: %s", CERTIFICATE_PATH)
        return
    if not os.path.isfile(CERTIFICATE_KEY_PATH):
        _logger.error("Cannot find server certificate key: %s", CERTIFICATE_KEY_PATH)
        return

    try:
        converterwebapp._MainHandler.app_data = helpers.config.items_as_dict("APPLICATION")
    except:
        _logger.error("Error fetching application data", exc_info=True)
        sys.exit(helpers.ExitCode.FAILURE)
    jobmonitorserver_settings = helpers.config.items_as_dict("JOBMONITOR_SERVER")
    helpers.make_dir_if_not_exists(jobmonitorserver_settings["download_dir"])

    try:
        tornado.options.parse_command_line()

        # set up converter server
        def start_http_server():
            _logger.info('Starting Converter Web Server...')
            temp = jobmonitorserver_settings.copy()
            del temp["allowed_auth_keys"] # not used by web server
            settings = dict(
                debug=WEBSERVER_DEBUG_MODE_ENABLED,
                cookie_secret=WEBSERVER_COOKIE_SECRET,
                template_path=os.path.join(os.path.dirname(__file__), "templates"),
                static_path=os.path.join(os.path.dirname(__file__), "static"),
                xsrf_cookies=WEBSERVER_XSRF_COOKIES_ENABLED,
                jobmonitorserver=temp
            )
            if WEBSERVER_DEBUG_MODE_ENABLED:
                _logger.warn("-"*80)
                _logger.warn(" "*10 + "!!! DEBUG MODE ENABLED !!!")
                _logger.warn("-"*80)

            webapp = converterwebapp.ConverterWebApp(**settings)
            global web_server
            web_server = converterhttpserver.ConverterHTTPServer(webapp)
            web_server.listen(WEBSERVER_PORT)

        # set up job monitor server
        def start_tcp_server():
            _logger.info('Starting Job Monitor Server...')
            global tcp_server
            global tcp_io_loop
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH) #@UndefinedVariable
            ssl_ctx.load_cert_chain(certfile=CERTIFICATE_PATH, keyfile=CERTIFICATE_KEY_PATH)
            tcp_io_loop = tornado.ioloop.IOLoop()
            tcp_io_loop.make_current()
            tcp_server = jobmonitortcpserver.JobMonitorTCPServer(
                             settings=jobmonitorserver_settings,
                             io_loop=tcp_io_loop,
                             ssl_options=ssl_ctx)
            tcp_server.listen(JOBMONITORSERVER_PORT)
            tcp_io_loop.start()

        from thread import start_new_thread
        start_new_thread(start_http_server,())
        start_new_thread(start_tcp_server,())

        # set up signal handler
        signal.signal(signal.SIGTERM, sig_handler) #@UndefinedVariable
        signal.signal(signal.SIGINT, sig_handler) #@UndefinedVariable

        # start IOLoop
        tornado.ioloop.IOLoop.instance().start()
        _logger.debug('bye')
    except:
        _logger.error("Server crashed or unable to start server", exc_info=True)
        sys.exit(helpers.ExitCode.FAILURE)

if __name__ == "__main__":
    main()
