import xml.dom.minidom

class XmlWriter:
    def __init__(self, project_name):
        xml.dom.minidom.Element.oldwritexml = xml.dom.minidom.Element.writexml
        xml.dom.minidom.Element.writexml = newwritexml

        self.document = xml.dom.minidom.Document()
        self.project = self.create_project(project_name)

    def create_project(self, project_name):
        project = self.document.createElement("Content.Project")

        project_name_field = self.document.createElement("projectName")
        project_name_field.appendChild(self.document.createTextNode(project_name))
        project.appendChild(project_name_field)

        device_name = self.document.createElement("deviceName")
        device_name.appendChild(self.document.createTextNode("Scratch"))
        project.appendChild(device_name)

        android_version = self.document.createElement("androidVersion")
        android_version.appendChild(self.document.createTextNode("10"))
        project.appendChild(android_version)

        catroid_version_code = self.document.createElement("catroidVersionCode")
        catroid_version_code.appendChild(self.document.createTextNode("820"))
        project.appendChild(catroid_version_code)

        catroid_version_name = self.document.createElement("catroidVersionName")
        catroid_version_name.appendChild(self.document.createTextNode("0.6.0beta-820-debug"))
        project.appendChild(catroid_version_name)
        
        screen_height = self.document.createElement("screenHeight")
        screen_height.appendChild(self.document.createTextNode("360"))
        project.appendChild(screen_height)
        
        screen_width = self.document.createElement("screenWidth")
        screen_width.appendChild(self.document.createTextNode("480"))
        project.appendChild(screen_width)
        
        sprite_list = self.document.createElement("spriteList")
        project.appendChild(sprite_list)

        self.document.appendChild(project)

        return project

    def add_sprite(self, sprite_name):
        sprite_node = self.document.createElement("Content.Sprite")

        name_node = self.document.createElement("name")
        name_node.appendChild(self.document.createTextNode(sprite_name))
        sprite_node.appendChild(name_node)
        
        costume_data_list_node = self.document.createElement("costumeDataList")
        sprite_node.appendChild(costume_data_list_node)
        
        sound_list_node = self.document.createElement("soundList")
        sprite_node.appendChild(sound_list_node)
        
        script_list_node = self.document.createElement("scriptList")
        sprite_node.appendChild(script_list_node)

        self.project.getElementsByTagName('spriteList')[0].appendChild(sprite_node)

    def get_sprite_node(self, sprite_name):
        sprite_list_node = self.project.getElementsByTagName('spriteList')[0]
        sprite_nodes = sprite_list_node.getElementsByTagName('Content.Sprite')
        return filter(lambda node: node.getElementsByTagName('name')[0].firstChild.nodeValue == sprite_name, sprite_nodes)[0]

    def add_costume(self, name, filename, sprite_name):
        costume_data = self.document.createElement("Common.CostumeData")
        
        name_node = self.document.createElement("name")
        name_node.appendChild(self.document.createTextNode(name))
        costume_data.appendChild(name_node)
        
        filename_node = self.document.createElement("fileName")
        filename_node.appendChild(self.document.createTextNode(filename))
        costume_data.appendChild(filename_node)

        sprite_node = self.get_sprite_node(sprite_name)
        sprite_node.getElementsByTagName('costumeDataList')[0].appendChild(costume_data)

    def add_sound(self, name, filename, sprite_name):
        sound_info = self.document.createElement("Common.SoundInfo")
        
        name_node = self.document.createElement("name")
        name_node.appendChild(self.document.createTextNode(name))
        sound_info.appendChild(name_node)
        
        filename_node = self.document.createElement("fileName")
        filename_node.appendChild(self.document.createTextNode(filename))
        sound_info.appendChild(filename_node)

        sprite_node = self.get_sprite_node(sprite_name)
        sprite_node.getElementsByTagName('soundList')[0].appendChild(sound_info)

    def add_script(self, sprite_name, script_type, bricks_params, broadcasted_message = None):
        if script_type == 'BroadcastScript':
            script_node = self.document.createElement("Content.BroadcastScript")
            action_node = self.document.createElement("receivedMessage")
            action_node.appendChild(self.document.createTextNode(broadcasted_message))
            script_node.appendChild(action_node)

        elif script_type == 'StartScript':
            script_node = self.document.createElement("Content.StartScript")
                
        elif script_type == 'WhenScript':
            script_node = self.document.createElement("Content.WhenScript")
            action_node = self.document.createElement("action")
            action_node.appendChild(self.document.createTextNode("Tapped"))
            script_node.appendChild(action_node)
            
        brick_list_node = self.document.createElement("brickList")
        script_node.appendChild(brick_list_node)

        sprite_node = self.document.createElement("sprite")
        sprite_node.setAttribute("reference", "../../..")
        script_node.appendChild(sprite_node)

        sprite_node = self.get_sprite_node(sprite_name)
        sprite_node.getElementsByTagName('scriptList')[0].appendChild(script_node)

        for brick_params in bricks_params:
            brick_name, params = brick_params
            self.add_brick(brick_list_node, brick_name, params)


    def add_brick(self, brick_list_node, brick_name, params):
        brick_node = self.document.createElement(brick_name)
        brick_list_node.appendChild(brick_node)
        if brick_name == "Bricks.SetCostumeBrick":
            costume_data_node = self.document.createElement("costumeData")
            brick_node.appendChild(costume_data_node)
            costume_data_node.setAttribute("reference", self.get_path_to_costume(costume_data_node, params["costume_name"]))
        elif brick_name == "Bricks.PlaySoundBrick":
            sound_info_node = self.document.createElement("soundInfo")
            brick_node.appendChild(sound_info_node)
            sound_info_node.setAttribute("reference", self.get_path_to_sound(sound_info_node, params["sound_name"]))
        else:
            for key, value in params.items():
                brick_parameter_node = self.document.createElement(key)
                brick_parameter_node.appendChild(self.document.createTextNode(value))
                brick_node.appendChild(brick_parameter_node)
        sprite_node = self.document.createElement("sprite")
        sprite_node.setAttribute("reference", "../../../../..")
        brick_node.appendChild(sprite_node)
        return brick_node

    def get_path_to_costume(self, node, costume_name):
        path = ""
        while node.tagName != "Content.Sprite":
            path += "../"
            node = node.parentNode

        costume_list_node = node.getElementsByTagName('costumeDataList')[0]
        path += "costumeDataList/"

        for index, costume_node in enumerate(costume_list_node.childNodes):
            if costume_node.getElementsByTagName('name')[0].firstChild.nodeValue == costume_name:
                if index == 0:
                    path += "Common.CostumeData"
                else:
                    path += "Common.CostumeData[" + str(index) + "]"
                break
        else:
            raise Exception("No costume found")
            
        return path

    def get_path_to_sound(self, node, sound_name):
        path = ""
        while node.tagName != "Content.Sprite":
            path += "../"
            node = node.parentNode

        sound_list_node = node.getElementsByTagName('soundList')[0]
        path += "soundList/"

        for index, sound_node in enumerate(sound_list_node.childNodes):
            if sound_node.getElementsByTagName('name')[0].firstChild.nodeValue == sound_name:
                if index == 0:
                    path += "Common.SoundInfo"
                else:
                    path += "Common.SoundInfo[" + str(index) + "]"
                break
        else:
            raise Exception("No sound found")
            
        return path

    def write_to_file(self, path):
        projectcode_file = open(path, 'w')
        self.document.writexml(projectcode_file, addindent='  ', newl="\n")
        projectcode_file.close()
 
def newwritexml(self, writer, indent='', addindent='', newl=''):
    if len(self.childNodes) == 1 and self.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE:
        writer.write(indent)
        self.oldwritexml(writer)
        writer.write(newl)
    else:
        self.oldwritexml(writer, indent, addindent, newl)
