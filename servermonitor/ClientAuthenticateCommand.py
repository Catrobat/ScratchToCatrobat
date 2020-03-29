import json

from ClientCommand import ClientCommand
from websocketserver.protocol.command.command import COMMAND_AUTHENTICATE
from scratchtocatrobat.tools.logger import log
from websocketserver.protocol.message.base.base_message import BaseMessage

class ClientAuthenticateCommand(ClientCommand):
    def __init__(self, config_params):
        args = {ClientCommand.ArgumentType.CLIENT_ID: int(config_params.clientid)}
        ClientCommand.__init__(self, COMMAND_AUTHENTICATE, args)

    def execute(self, ws):
        data = self.to_json().encode('utf8')
        log.debug("AuthenticateCommand Sending {}".format(data))
        ws.send(data)
        result = ws.recv()
        log.debug("AuthenticateCommand Response Received {}".format(result))
        if ClientAuthenticateCommand.verify_response(result):
            log.info("Authentication successful")
        else:
            log.error("Bad Authentication response")

    @staticmethod
    def verify_response( encoded_response):
        response = json.JSONDecoder('utf8').decode(encoded_response)
        return response["type"] == BaseMessage.MessageType.CLIENT_ID
