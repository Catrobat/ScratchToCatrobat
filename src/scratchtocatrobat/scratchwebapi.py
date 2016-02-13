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
import sys, os, re
from urlparse import urlparse
from scratchtocatrobat import common
from tools import helpers
from org.jsoup import Jsoup, HttpStatusException
from java.net import SocketTimeoutException, SocketException
from java.io import IOException
import scratch

_log = common.log

def is_valid_project_url(project_url):
    scratch_base_url = helpers.config.get("SCRATCH_API", "project_base_url")
    _HTTP_PROJECT_URL_PATTERN = scratch_base_url + r'\d+/?'
    return re.match(_HTTP_PROJECT_URL_PATTERN, project_url)

def download_project(project_url, target_dir, progress_bar=None):
    def project_id_from_url(project_url):
        normalized_url = project_url.strip("/")
        project_id = os.path.basename(urlparse(normalized_url).path)
        return project_id

    # TODO: fix circular reference
    if not is_valid_project_url(project_url):
        scratch_base_url = helpers.config.get("SCRATCH_API", "project_base_url")
        raise common.ScratchtobatError("Project URL must be matching '{}'. Given: {}".format(scratch_base_url + '<project id>', project_url))
    assert len(os.listdir(target_dir)) == 0

    # TODO: consolidate with classes from scratch module
    project_id = project_id_from_url(project_url)
    project_code_url = helpers.config.get("SCRATCH_API", "project_url_template").format(project_id)
    project_file_path = os.path.join(target_dir, scratch._PROJECT_FILE_NAME)
    common.download_file(project_code_url, project_file_path)

    project = scratch.RawProject.from_project_folder_path(target_dir)
    if progress_bar != None:
        progress_bar.num_of_iterations = project.num_of_iterations_of_downloaded_project(progress_bar)
        progress_bar.update() # update since project.json already downloaded!

    from threading import Thread
    class ResourceDownloadThread(Thread):
        def run(self):
            resource_url = self._kwargs["resource_url"]
            target_dir = self._kwargs["target_dir"]
            md5_file_name = self._kwargs["md5_file_name"]
            progress_bar = self._kwargs["progress_bar"]
            resource_file_path = os.path.join(target_dir, md5_file_name)
            try:
                common.download_file(resource_url, resource_file_path)
            except (SocketTimeoutException, SocketException, IOException) as e:
                raise common.ScratchtobatError("Error with {}: '{}'".format(resource_url, e))
            verify_hash = helpers.md5_of_file(resource_file_path)
            assert verify_hash == os.path.splitext(md5_file_name)[0], "MD5 hash of response data not matching"
            if progress_bar != None: progress_bar.update()

    # schedule parallel downloads
    unique_resource_names = project.unique_resource_names
    resource_url_template = helpers.config.get("SCRATCH_API", "asset_url_template")
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
                       "resource_url": resource_url_template.format(md5_file_name),
                       "target_dir": target_dir,
                       "progress_bar": progress_bar }
            threads.append(ResourceDownloadThread(kwargs=kwargs))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        resource_index = next_resources_end_index
    assert reference_index == resource_index and reference_index == num_total_resources

_cached_jsoup_doc = None
def request_project_page_DOM_tree_as_jsoup_document_for(project_id):
    global _cached_jsoup_doc
    if _cached_jsoup_doc != None:
        _log.debug("Cache hit: Jsoup document!")
        return _cached_jsoup_doc

    scratch_base_url = helpers.config.get("SCRATCH_API", "project_base_url")
    retries = int(helpers.config.get("SCRATCH_API", "http_retries"))
    timeout = int(helpers.config.get("SCRATCH_API", "http_timeout"))
    backoff = int(helpers.config.get("SCRATCH_API", "http_backoff"))
    delay = int(helpers.config.get("SCRATCH_API", "http_delay"))
    user_agent = helpers.config.get("SCRATCH_API", "user_agent")
    scratch_project_url = scratch_base_url + str(project_id)
    if not is_valid_project_url(scratch_project_url):
        raise common.ScratchtobatError("Project URL must be matching '{}'. Given: {}".format(scratch_base_url + '<project id>', scratch_project_url))

    def retry_hook(exc, tries, delay):
        _log.warning("  Exception: {}\nRetrying after {}:'{}' in {} secs (remaining trys: {})".format(sys.exc_info()[0], type(exc).__name__, exc, delay, tries))

    @helpers.retry((HttpStatusException, SocketTimeoutException), delay=delay, backoff=backoff, tries=retries, hook=retry_hook)
    def request_doc(scratch_project_url, timeout, user_agent):
        connection = Jsoup.connect(scratch_project_url)
        connection.userAgent(user_agent)
        connection.timeout(timeout)
        return connection.get()

    try:
        jsoup_doc = request_doc(scratch_project_url, timeout, user_agent)
        _cached_jsoup_doc = jsoup_doc
        return jsoup_doc
    except SocketTimeoutException:
        _log.error("Retry limit exceeded: {}".format(sys.exc_info()[0]))
        return None
    except:
        _log.error("Unexpected error for URL: {}, {}".format(scratch_project_url, sys.exc_info()[0]))
        return None

# TODO: class instead of request functions
def request_project_name_for(project_id):
    doc = request_project_page_DOM_tree_as_jsoup_document_for(project_id)
    if doc == None:
        return None
    title = ""
    element = doc.select("html > head > title").first()
    if element is not None:
        title = element.text().strip()
    return title

def request_project_description_for(project_id):
    doc = request_project_page_DOM_tree_as_jsoup_document_for(project_id)
    if doc == None:
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
