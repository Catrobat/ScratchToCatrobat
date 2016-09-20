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

import sys
import os
import re
import json
from urlparse import urlparse
from scratchtocatrobat.tools import logger, helpers
from scratchtocatrobat.tools.helpers import ProgressType
from collections import namedtuple
from datetime import datetime

HTTP_RETRIES = int(helpers.config.get("SCRATCH_API", "http_retries"))
HTTP_BACKOFF = int(helpers.config.get("SCRATCH_API", "http_backoff"))
HTTP_DELAY = int(helpers.config.get("SCRATCH_API", "http_delay"))
HTTP_TIMEOUT = int(helpers.config.get("SCRATCH_API", "http_timeout"))
HTTP_USER_AGENT = helpers.config.get("SCRATCH_API", "user_agent")
SCRATCH_PROJECT_BASE_URL = helpers.config.get("SCRATCH_API", "project_base_url")
SCRATCH_PROJECT_REMIX_TREE_URL_TEMPLATE = helpers.config.get("SCRATCH_API", "project_remix_tree_url_template")
SCRATCH_PROJECT_IMAGE_URL_TEMPLATE = helpers.config.get("SCRATCH_API", "project_image_url_template")

_log = logger.log
_cached_jsoup_documents = {}
_cached_remix_info_data = {}


class ScratchProjectInfo(namedtuple("ScratchProjectInfo", "title owner image_url instructions " \
                                    "notes_and_credits tags views favorites loves modified_date " \
                                    "shared_date")):
    def as_dict(self):
        return dict(map(lambda s: (s, getattr(self, s).strftime("%Y-%m-%d") \
                                   if isinstance(getattr(self, s), datetime) else getattr(self, s)),
                        self._fields))


    def __str__(self):
        return str(self.as_dict())


class ScratchProjectVisibiltyState(object):
    # Note: never change these values here.
    #       They are used in HTTP-responses and used across platforms!
    UNKNOWN = 0
    PRIVATE = 1
    PUBLIC = 2

class ScratchWebApiError(Exception):
    pass

class ResponseDocumentWrapper(object):
    def __init__(self, document):
        self.wrapped_document = document

    def select_first_as_text(self, query):
        pass

    def select_all_as_text_list(self, query):
        pass

    def select_attributes_as_text_list(self, query, attribute_name):
        pass


def is_valid_project_url(project_url):
    scratch_base_url = helpers.config.get("SCRATCH_API", "project_base_url")
    _HTTP_PROJECT_URL_PATTERN = scratch_base_url + r'\d+/?'
    return re.match(_HTTP_PROJECT_URL_PATTERN, project_url)

def extract_project_id_from_url(project_url):
    normalized_url = project_url.strip("/")
    project_id = os.path.basename(urlparse(normalized_url).path)
    return project_id


def download_project_code(project_id, target_dir):
    # TODO: consolidate with classes from scratch module
    from scratchtocatrobat.tools import common
    from scratchtocatrobat.scratch import scratch
    project_code_url = helpers.config.get("SCRATCH_API", "project_url_template").format(project_id)
    project_file_path = os.path.join(target_dir, scratch._PROJECT_FILE_NAME)
    try:
        common.download_file(project_code_url, project_file_path)
    except common.ScratchtobatHTTP404Error as _:
        _log.error("This seems to be an old Scratch program! Scratch 1.x programs are not supported!")

def download_project(project_url, target_dir, progress_bar=None):
    # TODO: make this independent from Java
    from threading import Thread
    from java.net import SocketTimeoutException, SocketException, UnknownHostException
    from java.io import IOException
    from scratchtocatrobat.tools import common
    from scratchtocatrobat.scratch import scratch

    if not is_valid_project_url(project_url):
        scratch_base_url = helpers.config.get("SCRATCH_API", "project_base_url")
        raise ScratchWebApiError("Project URL must be matching '{}'. Given: {}".format(scratch_base_url + '<project id>', project_url))
    assert len(os.listdir(target_dir)) == 0

    project_id = extract_project_id_from_url(project_url)
    download_project_code(project_id, target_dir)

    project = scratch.RawProject.from_project_folder_path(target_dir)
    if progress_bar != None:
        progress_bar.expected_progress = project.expected_progress_of_downloaded_project(progress_bar)
        progress_bar.update(ProgressType.DOWNLOAD_CODE) # update due to download of project.json file

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
            if progress_bar != None:
                progress_bar.update(ProgressType.DOWNLOAD_MEDIA_FILE)

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

def request_project_page_as_Jsoup_document_for(project_id, retry_after_http_status_exception=True):
    global _cached_jsoup_documents

    from java.net import SocketTimeoutException, UnknownHostException
    from org.jsoup import Jsoup, HttpStatusException

    if project_id in _cached_jsoup_documents:
        _log.debug("Cache hit: Document!")
        return _cached_jsoup_documents[project_id]

    scratch_project_url = SCRATCH_PROJECT_BASE_URL + str(project_id)
    if not is_valid_project_url(scratch_project_url):
        raise ScratchWebApiError("Project URL must be matching '{}'. Given: {}".format(SCRATCH_PROJECT_BASE_URL + '<project id>', scratch_project_url))

    def retry_hook(exc, tries, delay):
        _log.warning("  Exception: {}\nRetrying after {}:'{}' in {} secs (remaining trys: {})".format(sys.exc_info()[0], type(exc).__name__, exc, delay, tries))

    exceptions_retry = (SocketTimeoutException, UnknownHostException)
    if retry_after_http_status_exception:
        exceptions_retry += (HttpStatusException, )

    @helpers.retry(exceptions_retry, delay=HTTP_DELAY, backoff=HTTP_BACKOFF, tries=HTTP_RETRIES, hook=retry_hook)
    def fetch_document(scratch_project_url, timeout, user_agent):
        connection = Jsoup.connect(scratch_project_url)
        connection.userAgent(user_agent)
        connection.timeout(timeout)
        return _ResponseJsoupDocumentWrapper(connection.get())

    try:
        document = fetch_document(scratch_project_url, HTTP_TIMEOUT, HTTP_USER_AGENT)
        if document != None:
            _cached_jsoup_documents[project_id] = document
        return document
    except HttpStatusException as e:
        raise e
    except:
        _log.error("Retry limit exceeded or an unexpected error occurred: {}".format(sys.exc_info()[0]))
        return None

# TODO: class instead of request functions
def request_is_project_available(project_id):
    from org.jsoup import HttpStatusException
    try:
        request_project_page_as_Jsoup_document_for(project_id, False)
        return True
    except HttpStatusException as e:
        if e.getStatusCode() == 404:
            _log.error("HTTP 404 - Not found! Project not available.")
            return False
        else:
            raise e

def request_project_title_for(project_id):
    return extract_project_title_from_document(request_project_page_as_Jsoup_document_for(project_id))

def request_project_image_url_for(project_id):
    return extract_project_image_url_from_document(request_project_page_as_Jsoup_document_for(project_id))

def request_project_owner_for(project_id):
    return extract_project_owner_from_document(request_project_page_as_Jsoup_document_for(project_id))

def request_project_instructions_for(project_id):
    return extract_project_instructions_from_document(request_project_page_as_Jsoup_document_for(project_id))

def request_project_notes_and_credits_for(project_id):
    return extract_project_notes_and_credits_from_document(request_project_page_as_Jsoup_document_for(project_id))

def request_project_remixes_for(project_id):
    global _cached_remix_info_data

    if project_id in _cached_remix_info_data:
        _log.debug("Cache hit: Remix tree data!")
        return _cached_remix_info_data[project_id]

    from scratchtocatrobat.tools import common
    scratch_project_remix_tree_url = SCRATCH_PROJECT_REMIX_TREE_URL_TEMPLATE.format(project_id)

    try:
        import tempfile
        with tempfile.NamedTemporaryFile() as tempf:
            common.download_file(scratch_project_remix_tree_url, tempf.name)
            tempf.flush()
            json_data_string = tempf.read()
            if json_data_string is None:
                return []

            json_data_string = unicode(json_data_string)

            try:
                json_data = json.loads(json_data_string)
            except Exception as e:
                json_data = []

            remix_info = extract_project_remixes_from_data(json_data, project_id)
            _cached_remix_info_data[project_id] = remix_info
            return remix_info

    except Exception as e:
        _log.warn("Cannot fetch remix tree data: " + str(e))
        return None
    except common.ScratchtobatHTTP404Error as _:
        _log.error("Cannot fetch remix tree data: HTTP-Status-Code 404")
        return None

def request_project_details_for(project_id):
    return extract_project_details_from_document(request_project_page_as_Jsoup_document_for(project_id))

def request_project_visibility_state_for(project_id):
    return extract_project_visibilty_state_from_document(request_project_page_as_Jsoup_document_for(project_id))


def extract_project_title_from_document(document):
    if document is None: return None

    extracted_text = document.select_first_as_text("html > head > title")
    if extracted_text is None: return None

    title = unicode(extracted_text).strip()
    appended_title_text = "on Scratch"
    if title.endswith(appended_title_text):
        title = title.split(appended_title_text)[0].strip()
    return title.encode('utf-8')

def extract_project_image_url_from_document(document):
    if document is None: return None

    extracted_text_list = document.select_attributes_as_text_list("div#scratch > img.image", "src")
    if extracted_text_list is None or len(extracted_text_list) == 0: return None

    image_url_of_project = unicode(extracted_text_list[0]).strip()
    if image_url_of_project.startswith("//"):
        image_url_of_project = image_url_of_project.replace("//", "https://")
    return image_url_of_project

def extract_project_owner_from_document(document):
    if document is None: return None
    extracted_text = document.select_first_as_text("span#owner")
    return unicode(extracted_text).replace("by ", "").strip().encode('utf-8') if extracted_text != None else None

def extract_project_instructions_from_document(document):
    if document is None: return None
    extracted_text = document.select_first_as_text("div#instructions > div.viewport > div.overview")
    return unicode(extracted_text).strip().encode('utf-8') if extracted_text != None else None

def extract_project_notes_and_credits_from_document(document):
    if document is None: return None
    extracted_text = document.select_first_as_text("div#description > div.viewport > div.overview")
    return unicode(extracted_text).strip().encode('utf-8') if extracted_text != None else None

def extract_project_remixes_from_data(tree_data, project_id):
    if tree_data is None or not isinstance(tree_data, dict) or tree_data == []:
        return []

    scratch_program_data = tree_data[str(project_id)]
    remixed_program_info = []
    for remixed_program_id in scratch_program_data["children"]:
        remixed_program_data = tree_data[remixed_program_id]
        remixed_program_id = int(remixed_program_id)
        remix_data = {}
        remix_data["id"] = remixed_program_id
        remix_data["title"] = unicode(remixed_program_data["title"]).strip().encode('utf-8').replace("  ", " ")
        remix_data["owner"] = unicode(remixed_program_data["username"]).strip()
        remix_data["image"] = SCRATCH_PROJECT_IMAGE_URL_TEMPLATE.format(remixed_program_id, 144, 108)
        remixed_program_info += [remix_data]
    return remixed_program_info

def extract_project_visibilty_state_from_document(document):
    extracted_text = document.select_first_as_text("div#share-bar > span")
    if extracted_text == "Sorry this project is not shared":
        return ScratchProjectVisibiltyState.PRIVATE
    elif extracted_text is not None:
        return ScratchProjectVisibiltyState.UNKNOWN
    else:
        return ScratchProjectVisibiltyState.PUBLIC

def extract_project_details_from_document(document, escape_quotes=True):
    if document is None: return None

    title = extract_project_title_from_document(document)
    if title is None: return None
    if escape_quotes: title = title.replace('"','\\"')

    owner = extract_project_owner_from_document(document)
    if owner is None: return None
    if escape_quotes: owner = owner.replace('"','\\"')

    image_url = extract_project_image_url_from_document(document)
    if image_url is None: return None

    instructions = extract_project_instructions_from_document(document)
    if escape_quotes: instructions = instructions.replace('"','\\"')
    notes_and_credits = extract_project_notes_and_credits_from_document(document)
    if escape_quotes: notes_and_credits = notes_and_credits.replace('"','\\"')
    tags = document.select_all_as_text_list("div#project-tags div.tag-box span.tag") or []

    extracted_text = document.select_first_as_text("div#total-views > span.views")
    if extracted_text is None: return None
    views = int(unicode(extracted_text).strip())

    extracted_text = document.select_first_as_text("div#stats > div.action > span.favorite")
    if extracted_text is None: return None
    favorites = int(unicode(extracted_text).strip())

    extracted_text = document.select_first_as_text("div#love-this > span.love")
    if extracted_text is None: return None
    loves = int(unicode(extracted_text).strip())

    extracted_text = document.select_first_as_text("div#fixed div.dates span.date-updated")
    if extracted_text is None: return None
    modified_date_str = unicode(extracted_text).replace("Modified:", "").strip()
    try:
        modified_date = datetime.strptime(modified_date_str, '%d %b %Y')
    except:
        modified_date = None

    extracted_text = document.select_first_as_text("div#fixed div.dates span.date-shared")
    if extracted_text is None: return None
    shared_date_str = unicode(extracted_text).replace("Shared:", "").strip()
    try:
        shared_date = datetime.strptime(shared_date_str, '%d %b %Y')
    except:
        shared_date = None

    return ScratchProjectInfo(title = title, owner = owner, image_url = image_url,
                              instructions = instructions, notes_and_credits = notes_and_credits,
                              tags = tags, views = views, favorites = favorites, loves = loves,
                              modified_date = modified_date, shared_date = shared_date)
