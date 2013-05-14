import xml.dom.minidom

from scratchreader import ScratchReader

# -------------- JSON KEYS --------------

OBJNAME_KEY = "objName"
SOUNDS_KEY = "sounds"
CUSTUMES_KEY = "costumes"
CHILDREN_KEY = "children"
SCRIPTS_KEY = "scripts"
INFO_KEY = "info"

# -------------- <program> --------------
CATROBAT_TAG_PROGRAM = "program" #root element

# -------------- <header> --------------

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


# -------------- <objectList> --------------

CATROBAT_TAG_OBJECTLIST = "objectList"

# -------------- <variables> --------------

CATROBAT_TAG_VARIABLES = "variables"
CATROBAT_TAG_OBJECTVARIABLELIST = "objectVariableList"

CATROBAT_TAG_PROGRAMVARIABLELIST = "programVariableList"


class CatrobatWriter(object):
    def __init__(self, json_dict):
        self.json_dict = json_dict
        self.document = xml.dom.minidom.Document()
        
    def process_dict(self):
        self.create_header()
        self.create_object_list()
        self.create_variables()
        
        
    def create_header(self):
        
        #<program>
        self.program = self.document.createElement(CATROBAT_TAG_PROGRAM)
        self.document.appendChild(self.program)
        
        #<header>
        self.header = self.document.createElement(CATROBAT_TAG_HEADER)
        self.program.appendChild(self.header)
        
        #<applicationBuildName></applicationBuildName>
        self.header.appendChild(self.document.createElement(CATROBAT_TAG_APPLICATIONBUILDNAME))
        
        # <applicationBuildNumber>0</applicationBuildNumber>
        app_build_number = self.document.createElement(CATROBAT_TAG_APPLICATIONBUILDNUMBER)
        app_build_number.appendChild(self.document.createTextNode("0"))
        self.header.appendChild(app_build_number)
        
        # <applicationName>Pocket Code</applicationName>
        app_name = self.document.createElement(CATROBAT_TAG_APPLICATIONNAME)
        app_name.appendChild(self.document.createTextNode("Pocket Code"))
        self.header.appendChild(app_name)

        # <applicationVersion>0.7.2beta</applicationVersion>
        app_build_number = self.document.createElement(CATROBAT_TAG_APPLICATIONVERSION)
        app_build_number.appendChild(self.document.createTextNode("0.7.2beta"))
        self.header.appendChild(app_build_number)
        
         # <catrobatLanguageVersion>0.7</catrobatLanguageVersion>
        cat_lang_ver = self.document.createElement(CATROBAT_TAG_LANGUAGEVERSION)
        cat_lang_ver.appendChild(self.document.createTextNode("0.7"))
        self.header.appendChild(cat_lang_ver)
        
        #<dateTimeUpload></dateTimeUpload>
        self.header.appendChild(self.document.createElement(CATROBAT_TAG_DATETIMEUPLOAD))
        
        #<description></description>
        self.header.appendChild(self.document.createElement(CATROBAT_TAG_DESCRIPTION))
        
        # <deviceName>unknown</deviceName>
        device_name = self.document.createElement(CATROBAT_TAG_DEVICENAME)
        device_name.appendChild(self.document.createTextNode("unknown"))
        self.header.appendChild(device_name)
        
        #<mediaLicense></mediaLicense>
        self.header.appendChild(self.document.createElement(CATROBAT_TAG_MEDIALICENCE))
        
        # <platform>Android</platform>
        platform = self.document.createElement(CATROBAT_TAG_DEVICENAME)
        platform.appendChild(self.document.createTextNode("Android"))
        self.header.appendChild(platform)
        
        # <platformVersion>10</platformVersion>
        platform_version = self.document.createElement(CATROBAT_TAG_PLATFORMVERSION)
        platform_version.appendChild(self.document.createTextNode("10"))
        self.header.appendChild(platform_version)
        
        #<programLicense></programLicense>
        self.header.appendChild(self.document.createElement(CATROBAT_TAG_PROGRAMLICENCE))
        
        
        # <programName>Scratch App</programName>
        prog_name = self.document.createElement(CATROBAT_TAG_PROGRAMNAME)
        prog_name.appendChild(self.document.createTextNode("Scratch App")) #todo get app name from filename e.g project.sb2
        self.header.appendChild(prog_name)
        
        # <programScreenshotManuallyTaken>false</programScreenshotManuallyTaken>
        prog_screen_taken = self.document.createElement(CATROBAT_TAG_PROGRAMSCREENSHOTMANUALLYTAKEN)
        prog_screen_taken.appendChild(self.document.createTextNode("false"))
        self.header.appendChild(prog_screen_taken)
        
        #<remixOf></remixOf>
        self.header.appendChild(self.document.createElement(CATROBAT_TAG_REMIXOF))
        
         # <screenHeight>800</screenHeight>
        screen_height = self.document.createElement(CATROBAT_TAG_SCREENHEIGHT)
        screen_height.appendChild(self.document.createTextNode("800"))
        self.header.appendChild(screen_height)
        
        # <screenWidth>600</screenWidth>
        screen_width = self.document.createElement(CATROBAT_TAG_SCREENWIDTH)
        screen_width.appendChild(self.document.createTextNode("600"))
        self.header.appendChild(screen_width)
        
        #<tags></tags>
        self.header.appendChild(self.document.createElement(CATROBAT_TAG_TAGS))
        
        #<url></url>
        self.header.appendChild(self.document.createElement(CATROBAT_TAG_URL))
        
        #<userHandle></userHandle>
        self.header.appendChild(self.document.createElement(CATROBAT_TAG_USERHANDLE))
            
    def create_object_list(self):
        #<objectList>
        self.object_list = self.document.createElement(CATROBAT_TAG_OBJECTLIST)
        self.program.appendChild(self.object_list)
        
    def create_variables(self):
        #<variables>
        self.variables = self.document.createElement(CATROBAT_TAG_VARIABLES)
        self.program.appendChild(self.variables)
        
        #<objectVariableList>
        self.object_variable_list = self.document.createElement(CATROBAT_TAG_OBJECTVARIABLELIST)
        self.variables.appendChild(self.object_variable_list)
        
        #<programVariableList>
        self.program_variable_list = self.document.createElement(CATROBAT_TAG_PROGRAMVARIABLELIST)
        self.variables.appendChild(self.program_variable_list)
        
        