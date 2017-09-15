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


class Message(object):
    class ArgumentType(object):
        MSG                        = "msg"
        JOB_ID                     = "jobID"
        JOB_TITLE                  = "jobTitle"
        JOB_IMAGE_URL              = "jobImageURL"
        LINES                      = "lines"
        PROGRESS                   = "progress"
        URL                        = "url"
        CACHED_UTC_DATE            = "cachedUTCDate"
        CATROBAT_LANGUAGE_VERSION  = "catLangVers"
        JOBS_INFO                  = "jobsInfo"
        CLIENT_ID                  = "clientID"


    class CategoryType(object):
        BASE             =  0
        JOB              =  1

        @classmethod
        def category_for_type(cls, message_obj):
            from websocketserver.protocol.message.base.base_message import BaseMessage
            from websocketserver.protocol.message.job.job_message import JobMessage
            category_type_map = {
                BaseMessage: cls.BASE,
                JobMessage:  cls.JOB,
            }
            for category_class, category in category_type_map.iteritems():
                if isinstance(message_obj, category_class):
                    return category
            raise RuntimeError("Unknown type of message: " + message_obj.__class__.__name__)


    def __init__(self, message_type, data={}):
        assert isinstance(message_type, int)
        assert isinstance(data, dict)
        self.category = Message.CategoryType.category_for_type(self)
        self.type = message_type
        self.data = data


    def as_dict(self):
        return self.__dict__

