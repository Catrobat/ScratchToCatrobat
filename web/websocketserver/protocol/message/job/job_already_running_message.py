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

from job_message import JobMessage


class JobAlreadyRunningMessage(JobMessage):

    def __init__(self, job_ID, job_title, job_image_url):
        super(JobAlreadyRunningMessage, self).__init__(JobMessage.MessageType.JOB_ALREADY_RUNNING, job_ID, {
            JobAlreadyRunningMessage.ArgumentType.JOB_TITLE: job_title,
            JobAlreadyRunningMessage.ArgumentType.JOB_IMAGE_URL: job_image_url
        })
