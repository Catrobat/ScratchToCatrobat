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
from websocketserver.protocol import protocol

_logger = logging.getLogger(__name__)


class Command(object):
    def execute(self, ctxt, args):
        raise NotImplementedError()

    def is_valid_client_ID(self, redis_connection, client_ID):
        if client_ID is None:
            return False
        client_ID_string = str(client_ID)
        if client_ID_string is None or int(client_ID_string) <= 0:
            return False
        last_client_ID = redis_connection.get("lastClientID")
        return last_client_ID != None and client_ID_string.isdigit() and int(client_ID_string) <= int(last_client_ID)

    def is_valid_job_ID(self, job_ID):
        return str(job_ID).isdigit() and int(job_ID) > 0

    def retrieve_new_client_ID(self, ctxt):
        redis_conn = ctxt.redis_connection
        # check if this is the first client -> then set lastClientID in database to 0
        if redis_conn.get("lastClientID") == None:
            redis_conn.set("lastClientID", 0)
        new_client_ID = redis_conn.incr("lastClientID")
        ctxt.handler.set_client_ID(new_client_ID) # map client ID to web socket handler
        return new_client_ID


# TODO: create new packet for this and only send updates...
def update_jobs_info_on_listening_clients(ctxt):
    import retrieve_jobs_info
    from websocketserver import websockethandler
    for client_ID, handler_list in websockethandler.ConverterWebSocketHandler.client_ID_open_sockets_map.iteritems():
        message = retrieve_jobs_info.RetrieveJobsInfoCommand().execute(ctxt, { "clientID": str(client_ID) })
        for handler in handler_list:
            handler.send_message(message)


class InvalidCommand(Command):
    def execute(self, ctxt, args):
        return protocol.ErrorMessage("Invalid command!")


def get_command(name):
    import set_client_id, schedule_job, retrieve_jobs_info
    COMMANDS = {
        'set_client_ID': set_client_id.SetClientIDCommand(),
        'retrieve_jobs_info': retrieve_jobs_info.RetrieveJobsInfoCommand(),
        'schedule_job': schedule_job.ScheduleJobCommand()
    }
    if not isinstance(name, (str, unicode)) or name not in COMMANDS:
        command = InvalidCommand()
    else:
        command = COMMANDS[name]
    return command
