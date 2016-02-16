#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2015 The Catrobat Team
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

class JsonKeys(object):
    class Request(object):
        CMD = "cmd"
        ARGS = "args"

        ARGS_CLIENT_ID = "clientID"
        ARGS_URL = "url"
        ARGS_FORCE = "force"
        allowed_arg_keys = [ARGS_CLIENT_ID, ARGS_URL, ARGS_FORCE]

        @classmethod
        def is_valid(cls, data):
            return (data is not None) and (cls.CMD in data) and (cls.ARGS in data)

        @classmethod
        def extract_allowed_args(cls, args):
            filtered_args = {}
            for key in cls.allowed_arg_keys:
                if key in args:
                    filtered_args[key] = args[key]
            return filtered_args

class Message(object):
    class Type(object):
        ERROR = 0
        JOB_FAILED = 1
        JOB_RUNNING = 2
        JOB_ALREADY_RUNNING = 3
        JOB_READY = 4
        JOB_OUTPUT = 5
        JOB_PROGRESS = 6
        JOB_FINISHED = 7
        JOB_DOWNLOAD = 8
        JOBS_INFO = 9
        CLIENT_ID = 10
        RENEW_CLIENT_ID = 11

    def __init__(self, message_type, data):
        self.type = message_type
        self.data = data

    def as_dict(self):
        return self.__dict__

#
# Note: At the moment scratch_project_ID always acts as jobID
#

class ErrorMessage(Message):
    def __init__(self, message):
        super(ErrorMessage, self).__init__(Message.Type.ERROR, { "msg": message })

class JobFailedMessage(Message):
    def __init__(self, job_ID):
        super(JobFailedMessage, self).__init__(Message.Type.JOB_FAILED, { "jobID": job_ID })

class JobRunningMessage(Message):
    def __init__(self, job_ID):
        super(JobRunningMessage, self).__init__(Message.Type.JOB_RUNNING, { "jobID": job_ID })

class JobAlreadyRunningMessage(Message):
    def __init__(self, job_ID):
        super(JobAlreadyRunningMessage, self).__init__(Message.Type.JOB_ALREADY_RUNNING, { "jobID": job_ID })

class JobReadyMessage(Message):
    def __init__(self, job_ID):
        super(JobReadyMessage, self).__init__(Message.Type.JOB_READY, { "jobID": job_ID })

class JobOutputMessage(Message):
    def __init__(self, job_ID, line):
        super(JobOutputMessage, self).__init__(Message.Type.JOB_OUTPUT, {
            "jobID": job_ID,
            "line": line
        })

class JobProgressMessage(Message):
    def __init__(self, job_ID, progress):
        super(JobProgressMessage, self).__init__(Message.Type.JOB_PROGRESS, {
            "jobID": job_ID,
            "progress": progress
        })

class JobFinishedMessage(Message):
    def __init__(self, job_ID):
        super(JobFinishedMessage, self).__init__(Message.Type.JOB_FINISHED, { "jobID": job_ID })

class JobDownloadMessage(Message):
    def __init__(self, job_ID, download_url):
        super(JobDownloadMessage, self).__init__(Message.Type.JOB_DOWNLOAD, {
            "jobID": job_ID,
            "url": download_url
        })

class JobsInfoMessage(Message):
    def __init__(self, jobs_info):
        super(JobsInfoMessage, self).__init__(Message.Type.JOBS_INFO, { "jobsInfo": jobs_info })

class ClientIDMessage(Message):
    def __init__(self, client_ID):
        super(ClientIDMessage, self).__init__(Message.Type.CLIENT_ID, { "clientID": client_ID })

class RenewClientIDMessage(Message):
    def __init__(self, client_ID):
        super(RenewClientIDMessage, self).__init__(Message.Type.RENEW_CLIENT_ID, { "clientID": client_ID })
