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

import os, sys
import urllib
sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "..", "src"))
from scratchtocatrobat import scratchwebapi

REDIS_JOB_KEY_TEMPLATE = "job#{}"
REDIS_LISTENING_CLIENT_JOB_KEY_TEMPLATE = "listeningClientsOfJob#{}"
REDIS_CLIENTS_NOT_YET_DOWNLOADED_JOB_KEY_TEMPLATE = "clientsNotYetDownloadedJob#{}"
REDIS_JOB_CLIENT_KEY_TEMPLATE = "jobsOfClient#{}"


def extract_width_and_height_from_scratch_image_url(url_string, job_ID):
    # example: https://cdn2.scratch.mit.edu/get_image/project/82443924_144x108.png?v=1467378495.35
    URL_parts = url_string.split(str(job_ID) + "_")
    if len(URL_parts) != 2:
        return 150, 150 # default
    width_string, height_string = URL_parts[1].split(".png")[0].split("x")
    return int(width_string), int(height_string)


def create_download_url(job_ID, client_ID, job_title):
    return "/download?job_id={}&client_id={}&fname={}" \
           .format(job_ID, client_ID, urllib.quote_plus(job_title))


class ResponseBeautifulSoupDocumentWrapper(scratchwebapi.ResponseDocumentWrapper):
    def select_first_as_text(self, query):
        result = self.wrapped_document.select(query)
        if result is None or not isinstance(result, list) or len(result) == 0:
            return None
        return result[0].get_text()

    def select_all_as_text_list(self, query):
        result = self.wrapped_document.select(query)
        if result is None:
            return None
        return [element.get_text() for element in result if element is not None]

    def select_attributes_as_text_list(self, query, attribute_name):
        result = self.wrapped_document.select(query)
        if result is None:
            return None
        return [element[attribute_name] for element in result if element is not None]
