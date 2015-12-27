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
from tornado.options import define, options

import converterhttpserver
import converterwebapp
import jobmonitortcpserver

import sys
import os.path
import signal
import time

sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "..", "src"))
from scratchtocatrobat.tools import helpers

define("port", default=8888, help="run on the given port", type=int)
MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 3
_logger = logging.getLogger(__name__)

def sig_handler(sig, frame):
    _logger.warning('Caught signal: %s', sig)
    tornado.ioloop.IOLoop.instance().add_callback_from_signal(shutdown)

def shutdown():
    _logger.info('Stopping TCP server')
    tcp_server.timer.stop()
    tcp_server.stop()
    _logger.info('Stopping HTTP server')
    web_server.stop()
    _logger.info('Will shutdown in %s seconds ...', MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
    io_loop = tornado.ioloop.IOLoop.instance()
    deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN

    def stop_io_loop():
        now = time.time()
        if now < deadline and (io_loop._callbacks or io_loop._timeouts):
            io_loop.add_timeout(now + 1, stop_io_loop)
        else:
            io_loop.stop()
            _logger.info('Shutdown')
    stop_io_loop()

def main():
    logging.basicConfig(
        filename=None,
        level=logging.DEBUG,
        format='%(asctime)s: %(levelname)7s: [%(name)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    try:
        # TODO: refactor this... simplify/pythonize mapping...
        app_data = helpers.application_info(["version", "build_name", "build_number"])
        converterwebapp._MainHandler.app_data["version"] = app_data[0]
        converterwebapp._MainHandler.app_data["buildName"] = app_data[1]
        converterwebapp._MainHandler.app_data["buildNumber"] = app_data[2]
    except:
        _logger.error("Error fetching application data", exc_info=True)
        sys.exit(helpers.ExitCode.FAILURE)

    try:
        # TODO: parse command line...
        tornado.options.parse_command_line()
        # set up converter server
        _logger.info('Starting Converter Web Server...')
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        webapp = converterwebapp.ConverterWebApp(**settings)
        global web_server
        web_server = converterhttpserver.ConverterHTTPServer(webapp)
        web_server.listen(options.port)

        # set up job monitor server
        _logger.info('Starting Job Monitor Server...')
        global tcp_server
        data_dir = helpers.config.get("PATHS", "data")
        import ssl
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(certfile=os.path.join(data_dir, "certificates", "server.crt"),
                                keyfile=os.path.join(data_dir, "certificates", "server.key"))
        tcp_server = jobmonitortcpserver.JobMonitorTCPServer(ssl_options=ssl_ctx)
        tcp_server.listen(20000)

        # set up signal handler
        signal.signal(signal.SIGTERM, sig_handler)
        signal.signal(signal.SIGINT, sig_handler)

        # start IOLoop
        tornado.ioloop.IOLoop.instance().start()
        _logger.debug('bye')
    except:
        _logger.error("Server crashed or unable to start server", exc_info=True)
        sys.exit(helpers.ExitCode.FAILURE)

if __name__ == "__main__":
    main()
