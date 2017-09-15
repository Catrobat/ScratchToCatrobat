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

from websocketserver.protocol.message import message


class JobMessage(message.Message):
    class MessageType(object):
        JOB_FAILED               =  0
        JOB_RUNNING              =  1
        JOB_ALREADY_RUNNING      =  2
        JOB_READY                =  3
        JOB_OUTPUT               =  4
        JOB_PROGRESS             =  5
        JOB_CONVERSION_FINISHED  =  6


        @classmethod
        def is_valid(cls, message_type):
            return message_type >= cls.JOB_FAILED and message_type <= cls.JOB_CONVERSION_FINISHED


    def __init__(self, message_type, job_ID, data={}):
        assert isinstance(message_type, int) and JobMessage.MessageType.is_valid(message_type)
        assert isinstance(job_ID, int)
        assert isinstance(data, dict)
        data[JobMessage.ArgumentType.JOB_ID] = job_ID
        super(JobMessage, self).__init__(message_type, data)
