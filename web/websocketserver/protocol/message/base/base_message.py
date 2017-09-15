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


class BaseMessage(message.Message):
    class MessageType(object):
        ERROR      =  0
        INFO       =  1
        CLIENT_ID  =  2

        @classmethod
        def is_valid(cls, message_type):
            return message_type >= cls.ERROR and message_type <= cls.CLIENT_ID

    def __init__(self, message_type, data={}):
        assert isinstance(message_type, int) and BaseMessage.MessageType.is_valid(message_type)
        assert isinstance(data, dict)
        super(BaseMessage, self).__init__(message_type, data)
