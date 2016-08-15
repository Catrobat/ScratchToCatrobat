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

"""
  Simple web socket server for handling conversion requests.
"""

import logging
import tornado.web #@UnresolvedImport
from tornado import httputil, httpclient #@UnresolvedImport
from bs4 import BeautifulSoup #@UnresolvedImport
import os.path
from tornado.web import HTTPError #@UnresolvedImport
import sys
from datetime import datetime as dt, timedelta
sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "..", "src"))
from scratchtocatrobat import scratchwebapi
from scratchtocatrobat.scratchwebapi import ScratchProjectVisibiltyState
from scratchtocatrobat.tools import helpers
import helpers as webhelpers
from websocketserver.protocol.command.schedule_job_command import remove_client_from_download_list_if_exists
import redis #@UnresolvedImport

_logger = logging.getLogger(__name__)

# TODO: check if redis is available => error!
REDIS_CONNECTION = redis.Redis() #'127.0.0.1', 6789) #, password='secret')

CATROBAT_FILE_EXT = helpers.config.get("CATROBAT", "file_extension")
HTTP_RETRIES = int(helpers.config.get("SCRATCH_API", "http_retries"))
HTTP_BACKOFF = int(helpers.config.get("SCRATCH_API", "http_backoff"))
HTTP_DELAY = int(helpers.config.get("SCRATCH_API", "http_delay"))
HTTP_TIMEOUT = int(helpers.config.get("SCRATCH_API", "http_timeout"))
HTTP_USER_AGENT = helpers.config.get("SCRATCH_API", "user_agent")
SCRATCH_PROJECT_BASE_URL = helpers.config.get("SCRATCH_API", "project_base_url")


class _MainHandler(tornado.web.RequestHandler):
    app_data = {}
    def get(self):
        self.render("index.html", data=_MainHandler.app_data)


class _DownloadHandler(tornado.web.RequestHandler):
    def get(self):
        job_ID_string = self.get_query_argument("job_id", default=None)
        client_ID_string = self.get_query_argument("client_id", default=None)

        # TODO: use validation function instead...
        if job_ID_string == None or not job_ID_string.isdigit() \
        or client_ID_string == None or not client_ID_string.isdigit():
            raise HTTPError(404)

        job_ID = int(job_ID_string)
        client_ID = int(client_ID_string)

        file_dir = self.application.settings["jobmonitorserver"]["download_dir"]
        file_name = job_ID_string + CATROBAT_FILE_EXT
        file_path = "%s/%s" % (file_dir, file_name)

        if not file_name or not os.path.exists(file_path):
            raise HTTPError(404)

        remove_client_from_download_list_if_exists(REDIS_CONNECTION, job_ID, client_ID)
        file_size = os.path.getsize(file_path)
        self.set_header('Content-Type', 'application/zip')
        self.set_header('Content-Disposition', 'attachment; filename="%s"' % file_name)
        with open(file_path, "rb") as f:
            range_header = self.request.headers.get("Range")
            request_range = None
            if range_header:
                # TODO: implement own parse request range helper method
                request_range = httputil._parse_request_range(range_header, file_size)

            if request_range:
                # TODO: support HTTP range + test
                # TODO: request_range.end
                self.set_header('Content-Range', 'bytes {}-{}/{}'.format(request_range.start, (file_size - 1), file_size))
                self.set_header('Content-Length', file_size - request_range.start + 1)#(request_range.end - request_range.start + 1))
                file.seek(request_range.start)
            else:
                self.set_header('Content-Length', file_size)

            try:
                while True:
                    write_buffer = f.read(4096) # XXX: what if file is smaller than this buffer-size?
                    if write_buffer:
                        self.write(write_buffer)
                    else:
                        self.finish()
                        return
            except:
                raise HTTPError(404)
        raise HTTPError(500)


class ProjectDataResponse(object):

    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self):
        self.accessible = True
        self.visibility_state = ScratchProjectVisibiltyState.UNKNOWN
        self.project_data = {}
        self.valid_until = None

    def as_dict(self):
        cls = self.__class__
        return {
            "accessible": self.accessible,
            "visibility": self.visibility_state,
            "projectData": self.project_data,
            "validUntil": None if not self.valid_until else self.valid_until.strftime(cls.DATETIME_FORMAT)
        }


class _ProjectHandler(tornado.web.RequestHandler):
    response_cache = {}
    CACHE_ENTRY_VALID_FOR = 600 # 10 minutes (in seconds)

    @tornado.gen.coroutine
    def get(self, project_id = None):
        # ------------------------------------------------------------------------------------------
        # Featured projects HTTP-request
        # ------------------------------------------------------------------------------------------
        if project_id is None:
            # TODO: automatically update featured projects...
            self.write({ "results": webhelpers.FEATURED_SCRATCH_PROGRAMS })
            return

        # ------------------------------------------------------------------------------------------
        # Project details HTTP-request
        # ------------------------------------------------------------------------------------------
        cls = self.__class__
        if project_id in cls.response_cache and dt.now() <= cls.response_cache[project_id].valid_until:
            _logger.info("Cache hit for project ID {}".format(project_id))
            self.write(cls.response_cache[project_id].as_dict())
            return

        try:
            scratch_project_url = SCRATCH_PROJECT_BASE_URL + str(project_id)
            _logger.info("Fetching project info from: {}".format(scratch_project_url))
            http_response = yield self.application.async_http_client.fetch(scratch_project_url)
        except tornado.httpclient.HTTPError, e:
            _logger.warn("Unable to download project's web page: HTTP-Status-Code: " + str(e.code))
            response = ProjectDataResponse()
            if e.code == 404:
                # 'HTTP 404 - Not found' means not accessible
                # (e.g. projects that have been removed in the meanwhile...)
                response.accessible = False
                response.valid_until = dt.now() + timedelta(seconds=cls.CACHE_ENTRY_VALID_FOR)
                cls.response_cache[project_id] = response

            self.write(response.as_dict())
            return

        if http_response is None or http_response.body is None or not isinstance(http_response.body, (str, unicode)):
            _logger.error("Unable to download web page of project: Invalid or empty HTML-content!")
            self.write(ProjectDataResponse().as_dict())
            return

        #body = re.sub("(.*" + re.escape("<li>") + r'\s*'
        #     + re.escape("<div class=\"project thumb\">")
        #     + r'.*' + re.escape("<span class=\"owner\">") + r'.*'
        #     + re.escape("</span>") + r'\s*' + ")" + "(" + re.escape("</li>.*")
        #     + ")", r'\1</div>\2', http_response.body)
        document = webhelpers.ResponseBeautifulSoupDocumentWrapper(BeautifulSoup(http_response.body, b'html5lib'))
        visibility_state = scratchwebapi.extract_project_visibilty_state_from_document(document)
        response = ProjectDataResponse()
        response.accessible = True
        response.visibility_state = visibility_state
        response.valid_until = dt.now() + timedelta(seconds=cls.CACHE_ENTRY_VALID_FOR)

        if visibility_state != ScratchProjectVisibiltyState.PUBLIC:
            _logger.warn("Not allowed to access non-public scratch-project!")
            cls.response_cache[project_id] = response
            self.write(response.as_dict())
            return

        project_info = scratchwebapi.extract_project_details_from_document(document)
        if project_info is None:
            _logger.error("Unable to parse project-info from web page: Invalid or empty HTML-content!")
            self.write(response.as_dict())
            return

        response.project_data = project_info.as_dict()
        cls.response_cache[project_id] = response
        self.write(response.as_dict())
        return


class ConverterWebApp(tornado.web.Application):
    def __init__(self, **settings):
        from websocketserver import websockethandler
        self.settings = settings
        websockethandler.ConverterWebSocketHandler.REDIS_CONNECTION = REDIS_CONNECTION
        handlers = [
            (r"/", _MainHandler),
            (r"/download", _DownloadHandler),
            (r"/convertersocket", websockethandler.ConverterWebSocketHandler),
            (r"/api/v1/projects/?", _ProjectHandler),
            (r"/api/v1/projects/(\d+)/?", _ProjectHandler),
        ]
        httpclient.AsyncHTTPClient.configure(None, defaults=dict(user_agent=HTTP_USER_AGENT))
        self.async_http_client = httpclient.AsyncHTTPClient()
        tornado.web.Application.__init__(self, handlers, **settings)

