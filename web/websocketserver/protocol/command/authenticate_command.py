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

import logging
from command import Command
from websocketserver.protocol.message.base.client_id_message import ClientIDMessage

_logger = logging.getLogger(__name__)


class AuthenticateCommand(Command):

    def execute(self, ctxt, args):
        client_ID = args[Command.ArgumentType.CLIENT_ID]
        if not self.is_valid_client_ID(ctxt.redis_connection, client_ID):
            client_ID = self.retrieve_new_client_ID(ctxt)
            _logger.info("New client ID is: %d", client_ID)
            return ClientIDMessage(client_ID)

        _logger.info("Used client ID is: %d", client_ID)
        ctxt.handler.set_client_ID(client_ID) # map client ID to web socket handler
        assert ctxt.handler.get_client_ID() == client_ID
        return ClientIDMessage(client_ID)
