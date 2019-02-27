#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2017 The Catrobat Team
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
from collections import namedtuple
from datetime import datetime, timedelta

HTTP_RETRIES = int(helpers.config.get("SCRATCH_API", "http_retries"))
HTTP_BACKOFF = int(helpers.config.get("SCRATCH_API", "http_backoff"))
HTTP_DELAY = int(helpers.config.get("SCRATCH_API", "http_delay"))
HTTP_TIMEOUT = int(helpers.config.get("SCRATCH_API", "http_timeout"))
HTTP_USER_AGENT = helpers.config.get("SCRATCH_API", "user_agent")
SCRATCH_PROJECT_BASE_URL = helpers.config.get("SCRATCH_API", "project_base_url")
SCRATCH_PROJECT_REMIX_TREE_URL_TEMPLATE = helpers.config.get("SCRATCH_API", "project_remix_tree_url_template")
SCRATCH_PROJECT_IMAGE_BASE_URL = helpers.config.get("SCRATCH_API", "project_image_base_url")
SCRATCH_PROJECT_META_DATA_BASE_URL = helpers.config.get("SCRATCH_API", "project_meta_data_base_url")

_log = logger.log
_cached_jsoup_documents = {}
_cached_remix_info_data = {}

_projectMetaData = {}

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
    scratch_base_url_meta_data = helpers.config.get("SCRATCH_API", "project_meta_data_base_url")
    scratch_base_url_projects = helpers.config.get("SCRATCH_API", "internal_project_base_url")

    _HTTP_BASE_URL_PATTERN = scratch_base_url + r'\d+/?'
    _HTTP_META_URL_PATTERN = scratch_base_url_meta_data + r'\d+/?'
    _HTTP_PROJECT_URL_PATTERN = scratch_base_url_projects+"/" + r'\d+/?'
    is_valid = project_url.startswith("https://") and \
               (re.match(_HTTP_BASE_URL_PATTERN, project_url) or
                re.match(_HTTP_META_URL_PATTERN, project_url) or
                re.match(_HTTP_PROJECT_URL_PATTERN, project_url) )
    if not is_valid:
        raise ScratchWebApiError("Project URL must be matching '{}' or '{}' or '{}'. Given: {}".format(scratch_base_url + '<project id>', scratch_base_url_meta_data + '<project id>', scratch_base_url_projects + '<project id>', project_url))

    return is_valid

def extract_project_id_from_url(project_url):
    normalized_url = project_url.strip("/")
    project_id = os.path.basename(urlparse(normalized_url).path)
    return project_id


def download_project_code(project_id, target_dir):
    # TODO: consolidate with classes from scratch module
    from scratchtocatrobat.tools import common
    from scratchtocatrobat.scratch import scratch
    project_code_url = helpers.config.get("SCRATCH_API", "project_url_template").format(project_id)
    is_valid_project_url(project_code_url)
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

    is_valid_project_url(project_url)
    assert len(os.listdir(target_dir)) == 0

    project_id = extract_project_id_from_url(project_url)
    download_project_code(project_id, target_dir)
    return

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

def downloadProjectMetaData(project_id, retry_after_http_status_exception=False):
    global _projectMetaData
    import urllib2

    scratch_project_url = SCRATCH_PROJECT_META_DATA_BASE_URL + str(project_id)


    try:
        response = urllib2.urlopen(scratch_project_url,timeout=HTTP_TIMEOUT)
        html = response.read()
        document = json.loads(html)
        if document != None:
            document["meta_data_timestamp"] = datetime.now()
            _cached_jsoup_documents[project_id] = document
            _projectMetaData[project_id] = document
        return document
    except urllib2.HTTPError as e:
        if e.code == 404:
            _log.error("HTTP 404 - Not found! Project not available.")
            return None
        else:
            raise e
    except:
        _log.error("Retry limit exceeded or an unexpected error occurred: {}".format(sys.exc_info()[0]))
        return None

# TODO: class instead of request functions
def request_is_project_available(project_id):
    from org.jsoup import HttpStatusException
    try:
        return downloadProjectMetaData(project_id, False) is not None
    except HttpStatusException as e:
        if e.getStatusCode() == 404:
            _log.error("HTTP 404 - Not found! Project not available.")
            return False
        else:
            raise e


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
        remix_data["image"] = "{}{}.png".format(SCRATCH_PROJECT_IMAGE_BASE_URL, remixed_program_id)
        remixed_program_info += [remix_data]
    return remixed_program_info


def extract_project_details(project_id, escape_quotes=True):
    [title] = getMetaDataEntry(project_id , "title")
    if title is None: return None
    if escape_quotes: title = title.replace('"','\\"')

    [owner] = getMetaDataEntry(project_id , "username")
    if owner is None: return None
    if escape_quotes: owner = owner.replace('"','\\"')

    image_url = "{}{}.png".format(SCRATCH_PROJECT_IMAGE_BASE_URL, project_id)
    [instructions] = getMetaDataEntry(project_id , "instructions")
    if escape_quotes and instructions is not None: instructions = instructions.replace('"','\\"')
    [notes_and_credits] = getMetaDataEntry(project_id , "description")
    if escape_quotes and notes_and_credits is not None: notes_and_credits = notes_and_credits.replace('"','\\"')
    [stats] = getMetaDataEntry(project_id , "stats")
    remixes = stats["remixes"]
    extracted_text = stats["views"]
    if extracted_text is None: return None
    views = int(unicode(extracted_text).strip())

    extracted_text = stats["favorites"]
    if extracted_text is None: return None
    favorites = int(unicode(extracted_text).strip())

    extracted_text = stats["loves"]
    if extracted_text is None: return None
    loves = int(unicode(extracted_text).strip())

    [extracted_text] = getMetaDataEntry(project_id , "history")
    extracted_text = extracted_text["modified"]
    if extracted_text is None: return None
    modified_date_str = unicode(extracted_text).replace("Modified:", "").strip()
    try:
        modified_date = datetime.strptime(modified_date_str, '%d %b %Y')
    except:
        modified_date = None

    [extracted_text] = getMetaDataEntry(project_id , "history")
    extracted_text = extracted_text["shared"]
    if extracted_text is None: return None
    shared_date_str = unicode(extracted_text).replace("Shared:", "").strip()
    try:
        shared_date = datetime.strptime(shared_date_str, '%d %b %Y')
    except:
        shared_date = None

    return ScratchProjectInfo(title = title, owner = owner, image_url = image_url,
                              instructions = instructions, notes_and_credits = notes_and_credits,
                              tags = remixes, views = views, favorites = favorites, loves = loves,
                              modified_date = modified_date, shared_date = shared_date)




def getMetaDataEntry(projectID, *entryKey):
    try:
        global _projectMetaData
        if not projectID in _projectMetaData.keys() or (_projectMetaData[projectID]["meta_data_timestamp"] + timedelta(hours=1)) < datetime.now():
            downloadProjectMetaData(projectID)

        metadata = []


        for i in range(len(entryKey)):
            key = entryKey[i]
            try:
                if key == "visibility" and projectID not in _projectMetaData.keys():
                    metadata.append(ScratchProjectVisibiltyState.PRIVATE)
                elif key == "title" and projectID not in _projectMetaData.keys():
                    metadata.append("Untitled")
                elif key == "visibility":
                    metadata.append(ScratchProjectVisibiltyState.PUBLIC)
                elif key == "username":
                    metadata.append(_projectMetaData[projectID]["author"]["username"])
                else:
                    metadata.append(_projectMetaData[projectID][key])
            except:
                print(key)
                return [None]

        return metadata
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        # log error and continue without updating title and/or image URL!
        import logging

        logging.getLogger(__name__).error("Unexpected error at: {}, {}, {}, {}".format(sys.exc_info()[0], exc_type, fname, str(exc_tb.tb_lineno)))
