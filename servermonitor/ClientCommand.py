import json
from abc import abstractmethod, ABCMeta
__metaclass__ = ABCMeta


class ClientCommand:
    __metaclass__ = ABCMeta

    class ArgumentType(object):
        CLIENT_ID = "clientID"
        JOB_ID = "jobID"
        FORCE = "force"
        VERBOSE = "verbose"

    def __init__(self, command, arguments):
        self.cmd = command
        self.args = arguments
    cmd = None
    args = None

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    @abstractmethod
    def execute(self, ws):
        pass
