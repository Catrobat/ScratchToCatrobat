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
import json
import tornado.web
from tornado import httputil, httpclient
from bs4 import BeautifulSoup
import os.path
from tornado.web import HTTPError
import sys
from datetime import datetime as dt, timedelta
sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "..", "src"))
from scratchtocatrobat.scratch import scratchwebapi
from scratchtocatrobat.scratch.scratchwebapi import ScratchProjectVisibiltyState
from scratchtocatrobat.tools import helpers
import helpers as webhelpers
import redis

_logger = logging.getLogger(__name__)

REDIS_HOST = helpers.config.get("REDIS", "host")
REDIS_PORT = int(helpers.config.get("REDIS", "port"))
REDIS_PASSWORD = helpers.config.get("REDIS", "password")
REDIS_CONNECTION = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, encoding='utf-8')

CATROBAT_FILE_EXT = helpers.config.get("CATROBAT", "file_extension")
HTTP_RETRIES = int(helpers.config.get("SCRATCH_API", "http_retries"))
HTTP_BACKOFF = int(helpers.config.get("SCRATCH_API", "http_backoff"))
HTTP_DELAY = int(helpers.config.get("SCRATCH_API", "http_delay"))
HTTP_TIMEOUT = int(helpers.config.get("SCRATCH_API", "http_timeout"))
HTTP_USER_AGENT = helpers.config.get("SCRATCH_API", "user_agent")
SCRATCH_PROJECT_BASE_URL = helpers.config.get("SCRATCH_API", "project_base_url")
SCRATCH_PROJECT_REMIX_TREE_URL_TEMPLATE = helpers.config.get("SCRATCH_API", "project_remix_tree_url_template")
SCRATCH_PROJECT_MAX_NUM_REMIXES_TO_INCLUDE = int(helpers.config.get("CONVERTER_API", "max_num_remixes_to_include"))


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
                        _logger.info("Download of job {} finished (client: {})".format(job_ID, client_ID))
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
    RESPONSE_CACHE = {}
    CACHE_ENTRY_VALID_FOR = 1800 # 30 minutes (in seconds)
    IN_PROGRESS_FUTURE_MAP = {}

    def send_response_data(self, response_data):
        self.write(json.dumps(response_data).decode('unicode-escape').encode('utf8'))
        return

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
        project_id = int(project_id)
        if not webhelpers.is_valid_scratch_project_ID(project_id):
            x_real_ip = self.request.headers.get("X-Real-IP")
            _logger.error("Invalid project ID given: {}, IP: {}"
                          .format(project_id, x_real_ip or self.request.remote_ip))
            self.send_response_data({})
            return

        cls = self.__class__

        scratch_project_url = SCRATCH_PROJECT_BASE_URL + str(project_id)
        scratch_project_remix_tree_url = SCRATCH_PROJECT_REMIX_TREE_URL_TEMPLATE.format(project_id)

        if project_id in cls.RESPONSE_CACHE:
            response_data, valid_until = cls.RESPONSE_CACHE[project_id]
            if dt.now() <= valid_until:
                _logger.info("Cache hit for project ID {}".format(project_id))
                self.send_response_data(response_data)
                return

        try:
            if project_id in cls.IN_PROGRESS_FUTURE_MAP:
                futures = cls.IN_PROGRESS_FUTURE_MAP[project_id]
                _logger.info("SHARED FUTURE!")
                return
            else:
                async_http_client = self.application.async_http_client
                _logger.info("Fetching project and remix info from: {} and {} simultaneously"
                             .format(scratch_project_url, scratch_project_remix_tree_url))
                futures = [async_http_client.fetch(scratch_project_url),
                           async_http_client.fetch(scratch_project_remix_tree_url)]
                cls.IN_PROGRESS_FUTURE_MAP[project_id] = futures

            project_html_content, remix_tree_json_data = yield futures
        except tornado.httpclient.HTTPError, e:
            _logger.warn("Unable to download project's web page: HTTP-Status-Code: " + str(e.code))
            response = ProjectDataResponse()
            if e.code == 404:
                # 'HTTP 404 - Not found' means not accessible
                # (e.g. projects that have been removed in the meanwhile...)
                response.accessible = False
                response.valid_until = dt.now() + timedelta(seconds=cls.CACHE_ENTRY_VALID_FOR)
                cls.RESPONSE_CACHE[project_id] = (response.as_dict(), response.valid_until)
                if project_id in cls.IN_PROGRESS_FUTURE_MAP: del cls.IN_PROGRESS_FUTURE_MAP[project_id]
            self.send_response_data(response.as_dict())
            return
        except Exception, e:
            _logger.warn("Unable to download project's web page: " + str(e))
            self.send_response_data(ProjectDataResponse().as_dict())
            return

        if project_html_content is None or project_html_content.body is None \
        or not isinstance(project_html_content.body, (str, unicode)):
            _logger.error("Unable to download web page of project: Invalid or empty HTML-content!")
            self.send_response_data(ProjectDataResponse().as_dict())
            return

        document = webhelpers.ResponseBeautifulSoupDocumentWrapper(BeautifulSoup(project_html_content.body.decode('utf-8', 'ignore'), b'html5lib'))
        visibility_state = scratchwebapi.extract_project_visibilty_state_from_document(document)
        response = ProjectDataResponse()
        response.accessible = True
        response.visibility_state = visibility_state
        response.valid_until = dt.now() + timedelta(seconds=cls.CACHE_ENTRY_VALID_FOR)

        if visibility_state != ScratchProjectVisibiltyState.PUBLIC:
            _logger.warn("Not allowed to access non-public scratch-project!")
            cls.RESPONSE_CACHE[project_id] = (response.as_dict(), response.valid_until)
            if project_id in cls.IN_PROGRESS_FUTURE_MAP: del cls.IN_PROGRESS_FUTURE_MAP[project_id]
            self.send_response_data(response.as_dict())
            return

        project_info = scratchwebapi.extract_project_details_from_document(document, escape_quotes=True)
        if project_info is None:
            _logger.error("Unable to parse project-info from web page: Invalid or empty HTML-content!")
            self.send_response_data(response.as_dict())
            return

        remixed_program_info = []
        total_num_remixes = 0
        try:
            tree_data_string = unicode(remix_tree_json_data.body)
            tree_data = json.loads(tree_data_string)
            scratch_program_data = tree_data[str(project_id)]
            response.accessible = scratch_program_data["is_published"]
            response.visibility_state = ScratchProjectVisibiltyState.PUBLIC if scratch_program_data["visibility"] == "visible" else ScratchProjectVisibiltyState.PRIVATE
            remixed_program_info = scratchwebapi.extract_project_remixes_from_data(tree_data, project_id)
            total_num_remixes = len(remixed_program_info)
            remixed_program_info = remixed_program_info[:SCRATCH_PROJECT_MAX_NUM_REMIXES_TO_INCLUDE]
        except:
            _logger.error("Unable to decode JSON data of project: Invalid or empty JSON-content!")
        finally:
            response.project_data = project_info.as_dict()
            response_data = response.as_dict()
            response_data["projectData"]["total_num_remixes"] = total_num_remixes
            response_data["projectData"]["remixes"] = remixed_program_info
            cls.RESPONSE_CACHE[project_id] = (response_data, response.valid_until)
            if project_id in cls.IN_PROGRESS_FUTURE_MAP: del cls.IN_PROGRESS_FUTURE_MAP[project_id]
            self.send_response_data(response_data)


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

