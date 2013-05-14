import xml.dom.minidom
import os

from scratchreader import ScratchReader

# -------------- JSON KEYS --------------

OBJNAME_KEY = "objName"
SOUNDS_KEY = "sounds"
CUSTUMES_KEY = "costumes"
CHILDREN_KEY = "children"
SCRIPTS_KEY = "scripts"
INFO_KEY = "info"
SOUNDNAME_KEY = "soundName"
SOUNDID_KEY = "soundID"
MD5_KEY = "md5"
BASELAYERMD5_KEY = "baseLayerMD5"
BASELAYERID_KEY = "baseLayerID"
COSTUMENAME_KEY = "costumeName"



# ---------- CATROBAT XML TAGS ----------

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
CATROBAT_TAG_OBJECT = "object"
CATROBAT_TAG_LOOKLIST = "lookList"
CATROBAT_TAG_LOOK = "look"
CATROBAT_TAG_FILENAME = "fileName"
CATROBAT_TAG_NAME = "name"
CATROBAT_TAG_SCRIPTLIST = "scriptList"
CATROBAT_TAG_SOUNDLIST = "soundList"
CATROBAT_TAG_SOUND = "sound"

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
        platform = self.document.createElement(CATROBAT_TAG_PLATFORM)
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
        
        # <screenWidth>480</screenWidth>
        screen_width = self.document.createElement(CATROBAT_TAG_SCREENWIDTH)
        screen_width.appendChild(self.document.createTextNode("480"))
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
        self.process_sprite_list()
        
    def process_sprite_list(self):
        self.process_sprite(self.json_dict) #stage
        for child in self.json_dict[CHILDREN_KEY]:
            self.process_sprite(child)
    
    def process_sprite(self, sprite_dict):
        object = self.document.createElement(CATROBAT_TAG_OBJECT)
        self.object_list.appendChild(object)
        
        sound_list_node = self.process_sound_list(sprite_dict[SOUNDS_KEY])
        look_list_node = self.process_look_list(sprite_dict[CUSTUMES_KEY])
        
        object_name = self.document.createElement(CATROBAT_TAG_NAME)
        object_name.appendChild(self.document.createTextNode(sprite_dict[OBJNAME_KEY]))
        
        object.appendChild(look_list_node)
        object.appendChild(sound_list_node)
        object.appendChild(object_name)
        script_list_node = self.process_script_list(sprite_dict.get(SCRIPTS_KEY))
        object.appendChild(script_list_node)
    
    def process_script_list(self, script_list):
        script_list_node = self.document.createElement(CATROBAT_TAG_SCRIPTLIST)
        
        if script_list is not None:
            for script in script_list:
                script_node = self.process_script(script)
                if script_node is not None:
                    script_list_node.appendChild(script_node)
                
        return script_list_node

    def process_script(self):
        # NOT IMPLEMENTED YET
        return None

    def process_look_list(self, look_list):
        look_list_node = self.document.createElement(CATROBAT_TAG_LOOKLIST)
        
        for look_dict in look_list:
            look_node = self.process_look(look_dict)
            look_list_node.appendChild(look_node)
        
        return look_list_node  
        
    def process_look(self, look_dict):
        look_node = self.document.createElement(CATROBAT_TAG_LOOK)
        file_name_node = self.document.createElement(CATROBAT_TAG_FILENAME)
        file_name_node.appendChild(self.document.createTextNode(
            str(look_dict[BASELAYERID_KEY]) +  os.path.splitext(look_dict[BASELAYERMD5_KEY])[1]))
        
        name_node = self.document.createElement(CATROBAT_TAG_NAME)
        name_node.appendChild(self.document.createTextNode(look_dict[COSTUMENAME_KEY]))
        
        look_node.appendChild(file_name_node)
        look_node.appendChild(name_node)
        return look_node


    def process_sound_list(self, sound_list):
        sound_list_node = self.document.createElement(CATROBAT_TAG_SOUNDLIST)
        
        for sound_dict in sound_list:
            sound_node = self.process_sound(sound_dict)
            sound_list_node.appendChild(sound_node)
        
        return sound_list_node
    
    def process_sound(self, sound_dict):
        sound_node = self.document.createElement(CATROBAT_TAG_SOUND)
        file_name_node = self.document.createElement(CATROBAT_TAG_FILENAME)
        file_name_node.appendChild(self.document.createTextNode(
            str(sound_dict[SOUNDID_KEY]) +  os.path.splitext(sound_dict[MD5_KEY])[1]))
        
        name_node = self.document.createElement(CATROBAT_TAG_NAME)
        name_node.appendChild(self.document.createTextNode(sound_dict[SOUNDNAME_KEY]))
        
        sound_node.appendChild(file_name_node)
        sound_node.appendChild(name_node)
        return sound_node


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
        
        