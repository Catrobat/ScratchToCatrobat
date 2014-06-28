#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2014 The Catrobat Team
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
import hashlib
import os
import re
import socket
import urllib2
from urlparse import urlparse

from scratchtocatrobat import common
from scratchtocatrobat import scratch

# source: http://wiki.scratch.mit.edu/wiki/Scratch_File_Format_%282.0%29#Using_HTTP_requests
HTTP_PROJECT_API = "http://projects.scratch.mit.edu/internalapi/project/{}/get/"
# NOTE: without "projects." because at least svg files are not available with this domain
HTTP_ASSET_API = "http://scratch.mit.edu/internalapi/asset/{}/get/"
HTTP_PROJECT_URL_PREFIX = "http://scratch.mit.edu/projects/"
HTTP_PROJECT_URL_PATTERN = HTTP_PROJECT_URL_PREFIX + r'\d+/?'

_log = common.log


def download_project(project_url, target_dir):
    if not re.match(HTTP_PROJECT_URL_PATTERN, project_url):
        raise common.ScratchtobatError("Project URL must be matching '{}'. Given: {}".format(
            HTTP_PROJECT_URL_PREFIX + '<project id>', project_url))
    assert len(os.listdir(target_dir)) == 0

    def data_of_request_response(url):
        common.log.info("Requesting web api url: {}".format(url))
        def retry_hook(exc, tries, delay):
            _log.warning("  retrying after '%s' in %f secs (remaining trys: %d)", exc , delay, tries)

        @common.retry(socket.timeout, tries=3, hook=retry_hook)
        def request():
            return urllib2.urlopen(url, timeout=3).read()

        try:
            return request()
        except socket.timeout:
            # WORKAROUND: little more descriptive
            raise IOError("socket.timeout")

    def request_project_data(project_id):
        try:
            request_url = project_json_request_url(project_id)
            return data_of_request_response(request_url)
        except urllib2.HTTPError as e:
            raise common.ScratchtobatError("Error with {}: '{}'".format(request_url, e))

    def request_resource_data(md5_file_name):
        request_url = project_resource_request_url(md5_file_name)
        try:
            response_data = data_of_request_response(request_url)
            verify_hash = hashlib.md5(response_data).hexdigest()
            assert verify_hash == os.path.splitext(md5_file_name)[0], "MD5 hash of response data not matching"
            return response_data
        except urllib2.HTTPError as e:
            raise common.ScratchtobatError("Error with {}: '{}'".format(request_url, e))

    def project_json_request_url(project_id):
        return HTTP_PROJECT_API.format(project_id)

    def project_resource_request_url(md5_file_name):
        return HTTP_ASSET_API.format(md5_file_name)

    def project_id_from_url(project_url):
        normalized_url = project_url.strip("/")
        project_id = os.path.basename(urlparse(normalized_url).path)
        return project_id

    def write_to(data, file_path):
        with open(file_path, "wb") as fp:
            fp.write(data)

    def project_code_path(target_dir):
        return os.path.join(target_dir, scratch.SCRATCH_PROJECT_CODE_FILE)

    # TODO: consolidate with ProjectCode
    project_id = project_id_from_url(project_url)
    project_file_path = project_code_path(target_dir)
    write_to(request_project_data(project_id), project_file_path)
    project_code = scratch.ProjectCode(target_dir)
    for md5_file_name in project_code.resource_names:
        resource_file_path = os.path.join(target_dir, md5_file_name)
        write_to(request_resource_data(md5_file_name), resource_file_path)
