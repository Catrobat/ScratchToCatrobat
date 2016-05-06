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
from scratchtocatrobat import logger
from tools import helpers
from collections import namedtuple

HTTP_RETRIES = int(helpers.config.get("SCRATCH_API", "http_retries"))
HTTP_BACKOFF = int(helpers.config.get("SCRATCH_API", "http_backoff"))
HTTP_DELAY = int(helpers.config.get("SCRATCH_API", "http_delay"))
HTTP_TIMEOUT = int(helpers.config.get("SCRATCH_API", "http_timeout"))
HTTP_USER_AGENT = helpers.config.get("SCRATCH_API", "user_agent")
SCRATCH_PROJECT_BASE_URL = helpers.config.get("SCRATCH_API", "project_base_url")

class ScratchProjectInfo(namedtuple("ScratchProjectInfo", "title owner description views favorites loves remixes")):
    def as_dict(self):
        return dict((s, getattr(self, s)) for s in self._fields)
    def __str__(self):
        return str(self.as_dict())

_log = logger.log

class ScratchWebApiError(Exception):
    pass

class ResponseDocumentWrapper(object):
    def __init__(self, document):
        self.wrapped_document = document

    def select_first_as_text(self, query):
        pass

def is_valid_project_url(project_url):
    scratch_base_url = helpers.config.get("SCRATCH_API", "project_base_url")
    _HTTP_PROJECT_URL_PATTERN = scratch_base_url + r'\d+/?'
    return re.match(_HTTP_PROJECT_URL_PATTERN, project_url)

def download_project_code(project_id, target_dir):
    # TODO: consolidate with classes from scratch module
    from scratchtocatrobat import common
    import scratch
    project_code_url = helpers.config.get("SCRATCH_API", "project_url_template").format(project_id)
    project_file_path = os.path.join(target_dir, scratch._PROJECT_FILE_NAME)
    common.download_file(project_code_url, project_file_path)

def download_project(project_url, target_dir, progress_bar=None):
    # TODO: make this independent from Java
    from threading import Thread
    from java.net import SocketTimeoutException, SocketException, UnknownHostException
    from java.io import IOException
    from scratchtocatrobat import common
    import scratch

    # TODO: fix circular reference
    if not is_valid_project_url(project_url):
        scratch_base_url = helpers.config.get("SCRATCH_API", "project_base_url")
        raise ScratchWebApiError("Project URL must be matching '{}'. Given: {}".format(scratch_base_url + '<project id>', project_url))
    assert len(os.listdir(target_dir)) == 0

    def project_id_from_url(project_url):
        normalized_url = project_url.strip("/")
        project_id = os.path.basename(urlparse(normalized_url).path)
        return project_id

    project_id = project_id_from_url(project_url)
    download_project_code(project_id, target_dir)

    project = scratch.RawProject.from_project_folder_path(target_dir)
    if progress_bar != None:
        progress_bar.num_of_iterations = project.num_of_iterations_of_downloaded_project(progress_bar)
        progress_bar.update() # update due to download of project.json file

    class ResourceDownloadThread(Thread):
        def run(self):
            resource_url = self._kwargs["resource_url"]
            target_dir = self._kwargs["target_dir"]
            md5_file_name = self._kwargs["md5_file_name"]
            progress_bar = self._kwargs["progress_bar"]
            resource_file_path = os.path.join(target_dir, md5_file_name)
            try:
                common.download_file(resource_url, resource_file_path)
            except (SocketTimeoutException, SocketException, UnknownHostException, IOException) as e:
                raise ScratchWebApiError("Error with {}: '{}'".format(resource_url, e))
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

class _ResponseJsoupDocumentWrapper(ResponseDocumentWrapper):
    def select_first_as_text(self, query):
        result = self.wrapped_document.select(query).first()
        if result is None:
            return None
        return result.text()

    def select_all_as_text_list(self, query):
        result = self.wrapped_document.select(query)
        if result is None:
            return None
        return [element.text() for element in result if element is not None]

    def select_attributes_as_text_list(self, query, attribute_name):
        result = self.wrapped_document.select(query)
        if result is None:
            return None
        return [element.attr(attribute_name) for element in result if element is not None]

_cached_documents = {}
def request_project_page_as_Jsoup_document_for(project_id):
    global _cached_documents

    from java.net import SocketTimeoutException, UnknownHostException
    from org.jsoup import Jsoup, HttpStatusException

    if project_id in _cached_documents:
        _log.debug("Cache hit: Document!")
        return _cached_documents[project_id]

    scratch_project_url = SCRATCH_PROJECT_BASE_URL + str(project_id)
    if not is_valid_project_url(scratch_project_url):
        raise ScratchWebApiError("Project URL must be matching '{}'. Given: {}".format(SCRATCH_PROJECT_BASE_URL + '<project id>', scratch_project_url))

    def retry_hook(exc, tries, delay):
        _log.warning("  Exception: {}\nRetrying after {}:'{}' in {} secs (remaining trys: {})".format(sys.exc_info()[0], type(exc).__name__, exc, delay, tries))

    @helpers.retry((HttpStatusException, SocketTimeoutException, UnknownHostException), delay=HTTP_DELAY, backoff=HTTP_BACKOFF, tries=HTTP_RETRIES, hook=retry_hook)
    def fetch_document(scratch_project_url, timeout, user_agent):
        connection = Jsoup.connect(scratch_project_url)
        connection.userAgent(user_agent)
        connection.timeout(timeout)
        return _ResponseJsoupDocumentWrapper(connection.get())

    try:
        document = fetch_document(scratch_project_url, HTTP_TIMEOUT, HTTP_USER_AGENT)
        if document != None:
            _cached_documents[project_id] = document
        return document
    except:
        _log.error("Retry limit exceeded or an unexpected error occured: {}".format(sys.exc_info()[0]))
        return None

# TODO: class instead of request functions
def request_project_title_for(project_id):
    return extract_project_title_from_document(request_project_page_as_Jsoup_document_for(project_id))

def request_project_description_for(project_id):
    return extract_project_description_from_document(request_project_page_as_Jsoup_document_for(project_id))

def extract_project_title_from_document(document):
    if document is None:
        return None

    extracted_text = document.select_first_as_text("html > head > title")
    if extracted_text is None:
        return None

    title = unicode(extracted_text).strip()
    appended_title_text = "on Scratch"
    if title.endswith(appended_title_text):
        title = title.split(appended_title_text)[0].strip()
    return title

def extract_project_owner_from_document(document):
    if document is None:
        return None

    extracted_text = document.select_first_as_text("span#owner")
    if extracted_text is None:
        return None

    return unicode(extracted_text).strip()

def extract_project_description_from_document(document):
    if document is None:
        return None

    description = ""
    extracted_text = document.select_first_as_text("div#instructions > div.viewport > div.overview")
    if extracted_text != None:
        description += "-" * 40 + "\n"
        description += "Instructions:\n"
        description += unicode(extracted_text).strip() + "\n"
        description += "-" * 40

    extracted_text = document.select_first_as_text("div#description > div.viewport > div.overview")
    if extracted_text != None:
        description += "-" * 40 + "\n"
        description += "Description:\n"
        description += unicode(extracted_text).strip() + "\n"
        description += "-" * 40

    return description

def extract_project_remixes_from_document(document):
    if document is None:
        return None

    extracted_text_list = document.select_all_as_text_list("div.box > div.box-content > ul.media-col > li > div.project > span.title > a")
    if extracted_text_list is None:
        return None

    titles_of_remixed_projects = [unicode(text).strip() for text in extracted_text_list]

    extracted_text_list = document.select_all_as_text_list("div.box > div.box-content > ul.media-col > li > div.project > span.owner")
    if extracted_text_list is None:
        return None

    owners_of_remixed_projects = [unicode(text).replace("by ", "").strip() for text in extracted_text_list]

    extracted_text_list = document.select_attributes_as_text_list("div.box > div.box-content > ul.media-col > li > div.project > a.image > img", "src")
    if extracted_text_list is None:
        return None

    extracted_image_urls = [unicode(url).strip() for url in extracted_text_list]
    image_urls_of_remixed_projects = [url.replace("//", "https://") if url.startswith("//") else url for url in extracted_image_urls]

    has_unique_length = len(set([len(titles_of_remixed_projects), len(owners_of_remixed_projects), len(image_urls_of_remixed_projects)])) == 1
    if not has_unique_length:
        return None

    remixed_project_info = []
    for index, title in enumerate(titles_of_remixed_projects):
        data = {}
        data["title"] = title
        data["owner"] = owners_of_remixed_projects[index]
        data["image"] = image_urls_of_remixed_projects[index]
        remixed_project_info += [data]
    return remixed_project_info

def extract_project_details_from_document(document):
    if document is None:
        return None

    title = extract_project_title_from_document(document)
    if title is None:
        return None

    owner = extract_project_owner_from_document(document)
    if owner is None:
        return None

    description = extract_project_description_from_document(document)
    if description is None:
        return None

    extracted_text = document.select_first_as_text("div#stats > div.stats > div#total-views > span.views")
    if extracted_text is None:
        return None

    views = int(unicode(extracted_text).strip())

    extracted_text = document.select_first_as_text("div#stats > div.action > span.favorite")
    if extracted_text is None:
        return None

    favorites = int(unicode(extracted_text).strip())

    extracted_text = document.select_first_as_text("div#stats > div#love-this > span.love")
    if extracted_text is None:
        return None

    loves = int(unicode(extracted_text).strip())

    remixes = extract_project_remixes_from_document(document)
    if remixes is None:
        return None

    return ScratchProjectInfo(title = title, owner = owner, description = description, views = views,
                              favorites = favorites, loves = loves, remixes = remixes)
