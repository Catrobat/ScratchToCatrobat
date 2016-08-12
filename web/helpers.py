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


# TODO: remove theses data of default programs and fetch/update dynamically
FEATURED_SCRATCH_PROGRAMS = [{
    "id": 10205819,
    "title": "Dancin' in the Castle",
    "description": "First project on Scratch! This was great.",
    "instructions": "Click the flag to run the stack. Click the space bar to change it up!",
    "author": {
      "id": 2377748,
      "username": "jschombs"
    },
    "image": "https://cdn2.scratch.mit.edu/get_image/project/10205819_480x360.png",
    "history": {
      "created": "2013-05-13T18:04:20.000Z",
      "modified": "2013-05-13T18:48:30.000Z",
      "shared": "2013-05-13T18:49:03.000Z"
    },
    "stats": {
      "views": 96,
      "loves": 0,
      "favorites": 0,
      "comments": 0
    },
    "remix": {
      "root": None
    }
}, {
    "id": 82443924,
    "title": "Speed Drawing: Nessie (original species)",
    "description": "All drawn by me\nMusic: Candyland by Tobu\n\n ANSWERING FREQUENTLY ASKED " \
                   "QUESTIONS HERE:\n\n1. what program do I use?\nAnswer: I drew this here in "\
                   "scratch and used a Wacom intious pen and touch table. No fancy program \n\n2. "\
                   "Why won't the project load\/why does my computer crash?\nAnswer: there are  "\
                   "just too many costumes. \n\n3. How do you learn to draw like this?:\nAnswer: "\
                   "Practice ;)\n\n4. How do you make it to be speed drawn like that?\nAnswer: I "\
                   "first draw the first step as the first costume, then duplicate and each new "\
                   "costume that I duplicate will have more added to it.\nthen I give it my "\
                   "desired speed to make the costumes change fast.\n\n5. Do I do art "\
                   "request\/art trades?\nAnswer: not at the moment\n\n6. Is that suppose to be "\
                   "Nessie the lock ness monster?\nNo not intended to be. I just gave it that NAME.",
    "instructions": "Press the Green Flag (twice)       VVV (look below, please) VVV\n\n\n_______"\
                    "__________________________________________________\nThere is a total of 610 "\
                    "frames in this project.  I wasn't really surprise about the amounts of "\
                    "frames created but after seeing your guys' reaction im like \"oh my god, i "\
                    "can't believe i actually finished a project with 610 costumes\".\n",
    "author": {
      "id": 7648128,
      "username": "taffygirl13"
    },
    "image": "https://cdn2.scratch.mit.edu/get_image/project/82443924_480x360.png",
    "history": {
      "created": "2015-10-14T22:46:08.000Z",
      "modified": "2016-07-11T20:46:20.000Z",
      "shared": "2015-11-01T02:27:11.000Z"
    },
    "stats": {
      "views": 20581,
      "loves": 3172,
      "favorites": 2545,
      "comments": 0
    },
    "remix": {
      "root": None
    }
}, {
    "id": 18296306,
    "title": "Frozen VS Star Wars - The Movie",
    "description": "The Most Epic Battle Between FROZEN and Star Wars!!!!!! \n\nEnjoy!\n\nMore "\
                   "movies coming soon!!!!\n\nClips are from star wars and frozen youtube videos",
    "instructions": "Just Watch and Enjoy :)\n\nLeave a love-it if you loved the project :D",
    "author": {
      "id": 3351683,
      "username": "Elsa_The_Conqueror"
    },
    "image": "https://cdn2.scratch.mit.edu/get_image/project/18296306_480x360.png",
    "history": {
      "created": "2014-02-23T04:22:57.000Z",
      "modified": "2014-12-11T23:26:40.000Z",
      "shared": "2014-02-23T04:25:33.000Z"
    },
    "stats": {
      "views": 47871,
      "loves": 3180,
      "favorites": 2647,
      "comments": 0
    },
    "remix": {
      "root": None
    }
}]

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
