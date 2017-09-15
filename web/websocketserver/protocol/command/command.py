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

from websocketserver.protocol.message.base.error_message import ErrorMessage

COMMAND_AUTHENTICATE    = 0
COMMAND_RETRIEVE_INFO   = 1
COMMAND_SCHEDULE_JOB    = 2


class Command(object):
    class ArgumentType(object):
        CLIENT_ID = "clientID"
        JOB_ID    = "jobID"
        FORCE     = "force"
        VERBOSE   = "verbose"

    def execute(self, ctxt, args):
        raise NotImplementedError()

    def is_valid_client_ID(self, redis_connection, client_ID):
        if client_ID is None or not isinstance(client_ID, int) or client_ID <= 0:
            return False
        last_client_ID = redis_connection.get("lastClientID")
        return last_client_ID is not None and client_ID <= int(last_client_ID)

    def is_valid_job_ID(self, job_ID):
        return job_ID is not None and isinstance(job_ID, int) and job_ID > 0

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
    from websocketserver.protocol.command import retrieve_info_command
    from websocketserver import websockethandler
    for client_ID, handler_list in websockethandler.ConverterWebSocketHandler.client_ID_open_sockets_map.iteritems():
        message = retrieve_info_command.RetrieveInfoCommand().execute(ctxt, { "clientID": str(client_ID) })
        for handler in handler_list:
            handler.send_message(message)


class InvalidCommand(Command):
    def execute(self, ctxt, args):
        return ErrorMessage("Invalid command!")


def get_command(typeID):
    from websocketserver.protocol.command import authenticate_command
    from websocketserver.protocol.command import schedule_job_command
    from websocketserver.protocol.command import retrieve_info_command
    COMMANDS = {
        COMMAND_AUTHENTICATE:   authenticate_command.AuthenticateCommand(),
        COMMAND_RETRIEVE_INFO:   retrieve_info_command.RetrieveInfoCommand(),
        COMMAND_SCHEDULE_JOB:    schedule_job_command.ScheduleJobCommand()
    }
    return COMMANDS[typeID] if isinstance(typeID, int) and typeID in COMMANDS else InvalidCommand()
