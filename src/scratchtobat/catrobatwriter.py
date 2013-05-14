import xml.dom.minidom

from scratchreader import ScratchReader

OBJNAME_KEY = "objName"
SOUNDS_KEY = "sounds"
CUSTUMES_KEY = "costumes"
CHILDREN_KEY = "children"
SCRIPTS_KEY = "scripts"
INFO_KEY = "info"

CATROBAT_TAG_PROGRAM = "program" #root element

#header fields
CATROBAT_TAG_HEADER = "header"
CATROBAT_TAG_APPLICATIONBUILDNAME = "applicationBuildName"
CATROBAT_TAG_APPLICATIONBUILDNUMBER = "applicationBuildNumber"
CATROBAT_TAG_APPLICATIONNAME = "applicationName"
CATROBAT_TAG_APPLICATIONVERSION = "applicationVersion"
CATROBAT_TAG_LANGUAGEVERSION = "catrobatLanguageVersion"
CATROBAT_TAG_DATETIMEUPLOAD= "dateTimeUpload"
CATROBAT_TAG_DESCRIPTION  = "description"
CATROBAT_TAG_DEVICENAME= "deviceName"
CATROBAT_TAG_MEDIALICENCE= "mediaLicense"
CATROBAT_TAG_PLATFORM = "platform"
CATROBAT_TAG_PLATFORMVERSION = "platformVersion"
CATROBAT_TAG_PROGRAMLICENCE = "programLicense"
CATROBAT_TAG_PROGRAMNAME = "programName"
CATROBAT_TAG_PROGRAMSCREENSHOTMANUALLYTAKEN = "programScreenshotManuallyTaken"
CATROBAT_TAG_REMIXOF = "remixOf"
CATROBAT_TAG_SCREENHEIGHT = "screenHeight"
CATROBAT_TAG_SCREENWIDTH = "screenWidth"
CATROBAT_TAG_TAGS = "tags"
CATROBAT_TAG_URL = "url"
CATROBAT_TAG_USERHANDLE = "userHandle"



class CatrobatWriter(object):
    def __init__(self, json_dict):
        self.json_dict = json_dict
        self.document = xml.dom.minidom.Document()
        
    def process_dict(self):
        self.create_header()
        
        
    def create_header(self):
        self.program = self.document.createElement(CATROBAT_TAG_PROGRAM)
        self.document.appendChild(self.program)
        self.header = self.document.createElement(CATROBAT_TAG_HEADER)
        self.program.appendChild(self.header)
        
        #<applicationBuildName></applicationBuildName>
        self.header.appendChild(self.document.createElement(CATROBAT_TAG_APPLICATIONNAME))
        
        # <applicationBuildNumber>0</applicationBuildNumber>
        app_build_number = self.document.createElement(CATROBAT_TAG_APPLICATIONBUILDNUMBER)
        app_build_number.appendChild(self.document.createTextNode("0"))
        self.header.appendChild(app_build_number)
