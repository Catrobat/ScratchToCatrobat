import json

from ClientCommand import ClientCommand
from websocketserver.protocol.command.command import COMMAND_SCHEDULE_JOB
from scratchtocatrobat.tools.logger import log
from websocketserver.protocol.message.job import job_message

class ClientScheduleJobCommand(ClientCommand):
    def __init__(self, config_params):
        args = {ClientCommand.ArgumentType.JOB_ID: int(config_params.scractchprojectid),  ClientCommand.ArgumentType.FORCE:1}
        ClientCommand.__init__(self, COMMAND_SCHEDULE_JOB, args)

    def execute(self, ws):
        data = self.to_json().encode('utf8')
        log.debug("ScheduleJobCommand Sending {}".format(data))
        ws.send(data)
        response = ws.recv()
        log.debug("ScheduleJobCommand Response Received {}".format(response))
        if ClientScheduleJobCommand.verify_response(response):
            log.info("ScheduleJobCommand successful")
        else:
            log.error("Bad ScheduleJobCommand response")

    @staticmethod
    def verify_response(encoded_response):
        response = json.JSONDecoder('utf8').decode(encoded_response)
        return response["type"] != job_message.JobMessage.MessageType.JOB_FAILED