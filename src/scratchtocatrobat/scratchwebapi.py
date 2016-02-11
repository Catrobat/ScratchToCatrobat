#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2015 The Catrobat Team
#  (http://developer.catrobat.org/credits)
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
#  along with this program.  If not, see http://www.gnu.org/licenses/.
import hashlib
import sys, os, re, json
import urllib2
from urlparse import urlparse
from scratchtocatrobat import common
from tools import helpers
from org.jsoup import Jsoup, HttpStatusException
from java.net import SocketTimeoutException
from socket import timeout
from httplib import BadStatusLine

_log = common.log

class ProjectInfoKeys(object):
    PROJECT_DESCRIPTION = 'description'
    PROJECT_NAME = 'title'

def request_project_code(project_id):
    def project_json_request_url(project_id):
        return helpers.config.get("SCRATCH_API", "project_url_template").format(project_id)

    try:
        request_url = project_json_request_url(project_id)
        return common.url_response_data(request_url)
#     except urllib2.HTTPError as e:
    except None as e:
        raise common.ScratchtobatError("Error with {}: '{}'".format(request_url, e))

def is_valid_project_url(project_url):
    scratch_base_url = helpers.config.get("SCRATCH_API", "project_base_url")
    _HTTP_PROJECT_URL_PATTERN = scratch_base_url + r'\d+/?'
    return re.match(_HTTP_PROJECT_URL_PATTERN, project_url)

def download_project(project_url, target_dir, progress_bar=None):
    import scratch
    # TODO: fix circular reference
    scratch_base_url = helpers.config.get("SCRATCH_API", "project_base_url")
    if not is_valid_project_url(project_url):
        raise common.ScratchtobatError("Project URL must be matching '{}'. Given: {}".format(scratch_base_url + '<project id>', project_url))
    assert len(os.listdir(target_dir)) == 0

    def project_resource_request_url(md5_file_name):
        return helpers.config.get("SCRATCH_API", "asset_url_template").format(md5_file_name)

    def project_id_from_url(project_url):
        normalized_url = project_url.strip("/")
        project_id = os.path.basename(urlparse(normalized_url).path)
        return project_id

    def write_to(data, file_path):
        with open(file_path, "wb") as fp:
            fp.write(data)

    def project_code_path(target_dir):
        return os.path.join(target_dir, scratch._PROJECT_FILE_NAME)

    # TODO: consolidate with classes from scratch module
    project_id = project_id_from_url(project_url)
    project_file_path = project_code_path(target_dir)
    write_to(request_project_code(project_id), project_file_path)

    project = scratch.RawProject.from_project_folder_path(target_dir)
    if progress_bar != None:
        progress_bar.num_of_iterations = project.num_of_iterations_of_downloaded_project(progress_bar)
        progress_bar.update() # update since project.json already downloaded!

    from threading import Thread
    class ResourceDownloadThread(Thread):
        def request_resource_data(self, request_url):
            try:
                return common.url_response_data(request_url)
            except (timeout, urllib2.HTTPError, IOError, BadStatusLine) as e:
                raise common.ScratchtobatError("Error with {}: '{}'".format(request_url, e))

        def run(self):
            request_url = project_resource_request_url(self._kwargs["md5_file_name"])
            target_dir = self._kwargs["target_dir"]
            md5_file_name = self._kwargs["md5_file_name"]
            progress_bar = self._kwargs["progress_bar"]
            resource_file_path = os.path.join(target_dir, md5_file_name)
            response_data = self.request_resource_data(request_url)
            # FIXME: fails for some projects...
            verify_hash = hashlib.md5(response_data).hexdigest()
            assert verify_hash == os.path.splitext(md5_file_name)[0], "MD5 hash of response data not matching"
            write_to(response_data, resource_file_path)
            if progress_bar != None: progress_bar.update()

    # schedule parallel downloads
    unique_resource_names = project.unique_resource_names
    max_concurrent_downloads = int(helpers.config.get("SCRATCH_API", "http_max_concurrent_downloads"))
    resource_index = 0
    num_total_resources = len(unique_resource_names)
    reference_index = 0
    while resource_index < num_total_resources:
        num_next_resources = min(max_concurrent_downloads, (num_total_resources - resource_index))
        next_resources_end_index = resource_index + num_next_resources
        threads = []
        for index in range(resource_index, next_resources_end_index):
            assert index == reference_index
            reference_index += 1
            md5_file_name = unique_resource_names[index]
            kwargs = { "md5_file_name": md5_file_name,
                       "target_dir": target_dir,
                       "progress_bar": progress_bar }
            threads.append(ResourceDownloadThread(kwargs=kwargs))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        resource_index = next_resources_end_index
    assert reference_index == resource_index and reference_index == num_total_resources

def _project_info_request_url(project_id):
    return helpers.config.get("SCRATCH_API", "project_info_url_template").format(project_id)

def _request_project_info(project_id):
    # TODO: cache this request...
    response_data = common.url_response_data(_project_info_request_url(project_id))
    return json.loads(response_data)

# TODO: class instead of request functions
def request_project_name_for(project_id):
    return _request_project_info(project_id)[ProjectInfoKeys.PROJECT_NAME]

def request_project_description_for(project_id):
    scratch_base_url = helpers.config.get("SCRATCH_API", "project_base_url")
    retries = int(helpers.config.get("SCRATCH_API", "http_retries"))
    timeout = int(helpers.config.get("SCRATCH_API", "http_timeout"))
    scratch_project_url = scratch_base_url + str(project_id)
    if not is_valid_project_url(scratch_project_url):
        raise common.ScratchtobatError("Project URL must be matching '{}'. Given: {}".format(scratch_base_url + '<project id>', scratch_project_url))

    def retry_hook(exc, tries, delay):
        _log.warning("  Exception: {}\nRetrying after {}:'{}' in {} secs (remaining trys: {})".format(sys.exc_info()[0], type(exc).__name__, exc, delay, tries))

    @helpers.retry((HttpStatusException, SocketTimeoutException), delay=2, backoff=2, tries=retries, hook=retry_hook)
    def request_doc():
        connection = Jsoup.connect(scratch_project_url)
        connection.timeout(timeout)
        return connection.get()

    try:
        doc = request_doc()
    except SocketTimeoutException:
        _log.error("Retry limit exceeded: {}".format(sys.exc_info()[0]))
        return None
    except:
        _log.error("Unexpected error for URL: {}, {}".format(scratch_project_url, sys.exc_info()[0]))
        return None

    description = ""
    element = doc.select("div#instructions > div.viewport > div.overview").first()
    if element is not None:
        description += "-" * 40 + "\n"
        description += "Instructions:\n"
        description += element.text().strip() + "\n"
        description += "-" * 40

    element = doc.select("div#description > div.viewport > div.overview").first()
    if element is not None:
        description += "-" * 40 + "\n"
        description += "Description:\n"
        description += element.text().strip() + "\n"
        description += "-" * 40

    return description
