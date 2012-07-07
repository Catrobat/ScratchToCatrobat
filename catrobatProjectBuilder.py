import sys
import os
import shutil
import re
import tempfile
import hashlib
import subprocess
import time
import Image
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
        return filter(lambda node: node.getElementsByTagName('name')[0] == sprite_name, sprite_nodes)[0]

    def add_costume(self, name, filename, sprite_name):
        costume_data = self.document.createElement("Common.CostumeData")
        
        name_node = self.document.createElement("name")
        name_node.appendChild(self.document.createTextNode(costume))
        costume_data.appendChild(name_node)
        
        filename_node = self.document.createElement("fileName")
        filename_node.appendChild(self.document.createTextNode(filename))
        costume_data.appendChild(filename_node)

        sprite_node = self.get_sprite_node(sprite_name)
        sprite_node.getElementsByTagName('costumeDataList')[0].appendChild(costume_data)

    def add_sound(self, name, filename, sprite_name):

        sound_info = document.createElement("Common.SoundInfo")
        
        name_node = document.createElement("name")
        name_node.appendChild(document.createTextNode(sound))
        sound_info.appendChild(name_node)
        
        filename_node = document.createElement("fileName")
        filename_node.appendChild(document.createTextNode(filename))
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
            brick_list_node.appendChild(get_brick_node(brick_name, params))


    def get_brick_node(self, brick_name, params):
        brick_node = self.document.createElement(brick_name)
        for key, value in params.items():
            broadcast_message_node = self.document.createElement(key)
            broadcast_message_node.appendChild(self.document.createTextNode(value))
            brick_node.appendChild(broadcast_message_node)
        sprite_node = self.document.createElement("sprite")
        sprite_node.setAttribute("reference", "../../../../..")
        brick_node.appendChild(sprite_node)
        return brick_node

class ScratchOutputParser:
    def __init__(self, project_path, project_name):
        self.project_path = project_path
        self.project_name = project_name
        self.xml_writer = XmlWriter(project_name)

        self.TEMP_FOLDER = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.TEMP_FOLDER, 'images'))
        os.makedirs(os.path.join(self.TEMP_FOLDER, 'sounds'))

    def process_project(self):
        project_data = open(os.path.join(self.project_path, 'blocks.txt'), 'U').read()
        unparsed_sprites = project_data.split("\n\n\n")

        xml_writer.create_project(document, self.project_name)

        for unparsed_sprite in unparsed_sprites:
            if unparsed_sprite:
                sprite_info, unparsed_bricks = unparsed_sprite.split("\n\n", 1)
                sprite_name, variables, lists, position, visibility, sounds, costumes = sprite_info.split('\n')
                xml_writer.add_sprite(sprite_name)
                
                process_costumes(costumes, sprite_name)
                process_sounds(sounds, sprite_name)
                process_scripts(document, script_list_node, unparsed_bricks)
        
        projectcode_file = open(os.path.join(TEMP_FOLDER, 'projectcode.xml'), 'w')

        document.writexml(projectcode_file, addindent='  ', newl="\n")
        
        projectcode_file.close()

    def process_costumes(self, costumes, sprite_name):
        costumes = re.findall(r"'(.+?)'", costumes)
        costume_filenames = os.listdir(os.path.join(self.project_path, sprite_name, 'images'))
        for costume in costumes:
            for costume_filename in costume_filenames:
                if costume_filename.startswith(costume + '.'):
                    filename = costume_filename
                    break      

            Image.open(os.path.join(self.project_path, sprite_name, 'images', filename))\
                 .save(os.path.join(TEMP_FOLDER, 'images', sprite_name + '_' + costume + '.png'))

            filename = sprite_name + '_' + costume + '.png'

            file_contents = open(os.path.join(TEMP_FOLDER, 'images', filename), 'rb').read()
            checksum = hashlib.md5(file_contents).hexdigest().upper()

            os.rename(os.path.join(TEMP_FOLDER, 'images', filename),\
                      os.path.join(TEMP_FOLDER, 'images', checksum + '_' + filename))
            filename = checksum + '_' + filename

            xml_writer.add_costume(name, filename, sprite_name)

    def process_sounds(self, sounds, sprite_name):
        sounds = re.findall(r"'(.+?)'", sounds)
        sounds.remove('-')
        sounds.remove('record...')
        sounds_filenames = os.listdir(os.path.join(self.project_path, sprite_name, 'sounds'))
        for sound in sounds:
            for sound_filename in sounds_filenames:
                if sound_filename.startswith(sound + '.'):
                    filename = sound_filename
                    break      

            shutil.copy(os.path.join(self.project_path, sprite_name, 'sounds', filename),\
                        os.path.join(TEMP_FOLDER, 'sounds', sprite_name + '_' + sound_filename))

            filename = sprite_name + '_' + sound_filename

            file_contents = open(os.path.join(TEMP_FOLDER, 'sounds', filename), 'rb').read()
            checksum = hashlib.md5(file_contents).hexdigest().upper()

            os.rename(os.path.join(TEMP_FOLDER, 'sounds', filename),\
                      os.path.join(TEMP_FOLDER, 'sounds', checksum + '_' + filename))
            filename = checksum + '_' + filename

            xml_writer.add_costume(name, filename, sound_name)
    
    def process_scripts(self, unparsed_bricks, sprite_name):
        scripts_data = re.split(".*?EventHatMorph", unparsed_bricks)
        for script_data in scripts_data:
            if script_data:
                script_data = script_data.splitlines()
                if "'when I receive'" in script_data[0]:
                    script_type = 'BroadcastScript'
                elif "'when'" in script_data[0]:
                    if script_data[1] == "Scratch-StartClicked":
                        script_type = 'StartScript'
                    elif script_data[1] == "Scratch-MouseClickEvent":
                        script_type = 'WhenScript'
                    elif script_data[1] == "Scratch-KeyPressedEvent":
                        continue #TODO

                bricks_params = []
                while script_data:
                    brick_name = script_data.pop(0)
                    if "BlockMorph" in brick_name:
                        brick_name = script_data.pop(0)
                        if "'show'" in brick_name:
                            bricks_params.append(("Bricks.ShowBrick", {}))
                        elif "'hide'" in brick_name:
                            bricks_params.append(("Bricks.HideBrick", {}))
                        elif "broadcast %e" in brick_name:
                            script_data.pop(0)
                            message = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.BroadcastBrick", {"broadcastMessage": message}))
                        elif "wait %n secs" in brick_name:
                            script_data.pop(0)
                            time = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            time = str(long(float(time) * 1000))
                            bricks_params.append(("Bricks.WaitBrick", {"timeToWaitInMilliSeconds": time}))
                        elif "next costume" in brick_name:
                            bricks_params.append(("Bricks.NextCostumeBrick", {}))
                        elif "set size to %n%" in brick_name:
                            script_data.pop(0)
                            size = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.SetSizeToBrick", {"size": size}))
                        elif "change size by %n" in brick_name:
                            script_data.pop(0)
                            size = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.ChangeSizeByNBrick", {"size": size}))
                        elif "turn %n degrees" in brick_name:
                            direction = script_data.pop(0)
                            script_data.pop(0)
                            degrees = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            if "#turnLeft" in direction:
                                bricks_params.append(("Bricks.TurnLeftBrick", {"degrees": degrees}))
                            else:
                                bricks_params.append(("Bricks.TurnRightBrick", {"degrees": degrees}))
                        elif "go to x:%n y:%n" in brick_name:
                            script_data.pop(0)
                            x = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            y = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.PlaceAtBrick", {"xPosition": x, "yPosition": y}))
                        elif "switch to costume %l" in brick_name:
                            add_set_costume_brick(document, brick_list_node, script_data) ######################################
                        elif "play sound %S" in brick_name:
                            add_play_sound_brick(document, brick_list_node, script_data) ###########################
                        elif "set %g effect to %n" in brick_name:
                            script_data.pop(0)
                            effect = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            script_data.pop(0)
                            effect_value = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            if effect == 'brightness':
                                bricks_params.append(("Bricks.SetBrightnessBrick", {"brightness": effect_value}))
                            elif effect == 'ghost':
                                bricks_params.append(("Bricks.SetGhostEffectBrick", {"transparency": effect_value}))
                        elif "change %g effect to %n" in brick_name:
                            script_data.pop(0)
                            effect = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            script_data.pop(0)
                            effect_value = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            if effect == 'brightness':
                                bricks_params.append(("Bricks.ChangeBrightnessBrick", {"changeBrightness": effect_value}))
                            elif effect == 'ghost':
                                bricks_params.append(("Bricks.ChangeGhostEffectBrick", {"changeGhostEffect": effect_value}))
                        elif "stop all sounds" in brick_name:
                            bricks_params.append(("Bricks.StopAllSoundsBrick", {}))
                        elif "change volume by %n" in brick_name:
                            script_data.pop(0)
                            volume = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.ChangeVolumeByBrick", {"volume": volume}))
                        elif "set volume to %n%" in brick_name:
                            script_data.pop(0)
                            volume = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.SetVolumeToBrick", {"volume": volume}))
                        elif "say %s" in brick_name:
                            script_data.pop(0)
                            text = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.SpeakBrick", {"text": text}))
                        elif "set x to" in brick_name:
                            script_data.pop(0)
                            x = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.SetXBrick", {"xPosition": x}))
                        elif "set y to" in brick_name:
                            script_data.pop(0)
                            y = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.SetYBrick", {"yPosition": y}))
                        elif "change x by" in brick_name:
                            script_data.pop(0)
                            x = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.ChangeXByBrick", {"xMovement": x}))
                        elif "change y by" in brick_name:
                            script_data.pop(0)
                            y = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.ChangeYByBrick", {"yMovement": y}))
                        elif "point in direction %d" in brick_name:
                            script_data.pop(0)
                            degrees = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.PointInDirectionBrick", {"degrees": degrees}))
                        elif "glide %n secs to x:%n y:%n" in brick_name:
                            script_data.pop(0)
                            time = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            time = str(long(float(time) * 1000))
                            x = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            y = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.GlideToBrick", {"durationInMilliSeconds": time, "xDestination": x, "yDestination": y}))
                        elif "if on edge, bounce" in brick_name:
                            bricks_params.append(("Bricks.IfOnEdgeBounceBrick", {}))
                        elif "move %n steps" in brick_name:
                            script_data.pop(0)
                            steps = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.MoveNStepsBrick", {"steps": steps}))
                        elif "go to front" in brick_name:
                            bricks_params.append(("Bricks.ComeToFrontBrick", {}))
                        elif "go back %n layers" in brick_name:
                            script_data.pop(0)
                            steps = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.GoNStepsBackBrick", {"steps": steps}))
                        elif "point towards %m" in brick_name:
                            script_data.pop(0)
                            sprite_name = script_data.pop(0)
                            script_data.pop(0)
                            script_data.pop(0)
                            #brick_list_node.appendChild(get_brick_node(document, "Bricks.PointToBrick", {"pointedSprite": steps}))

                self.xml_writer.add_script('BroadcastScript', broadcasted_message=script_data[1])


def add_set_costume_brick(document, brick_list_node, script_data):
    script_data.pop(0)
    costume_name = re.findall(r"'(.+?)'", script_data.pop(0))[0]

    brick_node = document.createElement("Bricks.SetCostumeBrick")
    brick_list_node.appendChild(brick_node)
     
    sprite_node = document.createElement("sprite")
    sprite_node.setAttribute("reference", "../../../../..")
    brick_node.appendChild(sprite_node)

    costume_list_node = filter(lambda node: node.nodeName == "costumeDataList", brick_list_node.parentNode.parentNode.parentNode.childNodes)[0]

    for index, costume_node in enumerate(costume_list_node.childNodes):
        costume_name_node = filter(lambda node: node.nodeName == "name", costume_node.childNodes)[0]
        if costume_name_node.firstChild.nodeValue == costume_name:
            costume_data_node = document.createElement("costumeData")
            if index == 0:
                costume_data_node.setAttribute("reference", "../../../../../costumeDataList/Common.CostumeData")
            else:
                costume_data_node.setAttribute("reference", "../../../../../costumeDataList/Common.CostumeData[" + str(index) + "]")
            brick_node.appendChild(costume_data_node)
            break

def add_point_to_brick(document, brick_list_node, script_data):
    script_data.pop(0)
    sprite_name = re.findall(r"'(.+?)'", script_data.pop(0))[0]

    brick_node = document.createElement("Bricks.PointToBrick")
    brick_list_node.appendChild(brick_node)
     
    sprite_node = document.createElement("sprite")
    sprite_node.setAttribute("reference", "../../../../..")
    brick_node.appendChild(sprite_node)

    sprite_nodes = filter(lambda node: node.nodeName == "Content.Sprite", brick_list_node.parentNode.parentNode.parentNode.parentNode.childNodes)

    for index, sprite_node in enumerate(sprite_nodes.childNodes):
        sprite_name_node = costume_node.getElementsByTagName('name')[0]
        if sprite_node.firstChild.nodeValue == sprite_name:
            referenced_sprite_node = document.createElement("pointedSprite")
            if index == 0:
                referenced_sprite_node.setAttribute("reference", "../../../../../../Content.Sprite")
            else:
                referenced_sprite_node.setAttribute("reference", "../../../../../../Content.Sprite[" + str(index) + "]")
            brick_node.appendChild(referenced_sprite_node)
            break

def add_play_sound_brick(document, brick_list_node, script_data):
    script_data.pop(0)
    sound_name = re.findall(r"'(.+?)'", script_data.pop(0))[0]

    brick_node = document.createElement("Bricks.PlaySoundBrick")
    brick_list_node.appendChild(brick_node)
    
    sprite_node = document.createElement("sprite")
    sprite_node.setAttribute("reference", "../../../../..")
    brick_node.appendChild(sprite_node)

    sound_list_node = filter(lambda node: node.nodeName == "soundList", brick_list_node.parentNode.parentNode.parentNode.childNodes)[0]

    for index, costume_node in enumerate(sound_list_node.childNodes):
        sound_name_node = filter(lambda node: node.nodeName == "name", costume_node.childNodes)[0]
        if sound_name_node.firstChild.nodeValue == sound_name:
            soundinfo_node = document.createElement("soundInfo")
            if index == 0:
                soundinfo_node.setAttribute("reference", "../../../../../soundList/Common.SoundInfo")
            else:
                soundinfo_node.setAttribute("reference", "../../../../../soundList/Common.SoundInfo[" + str(index) + "]")
            brick_node.appendChild(soundinfo_node)
            break
 
def newwritexml(self, writer, indent='', addindent='', newl=''):
    if len(self.childNodes) == 1 and self.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE:
        writer.write(indent)
        self.oldwritexml(writer)
        writer.write(newl)
    else:
        self.oldwritexml(writer, indent, addindent, newl)

def main():
    if len(sys.argv) != 5:
        print 'Invalid arguments. Correct usage:'
        print 'python catrobatProjectBuilder.py <path_to_scratch_image> <path_to_scratch_project> <project_title> <path_to_output>'
        return 1
    path_to_scratch_image = sys.argv[1]
    path_to_scratch_project = sys.argv[2]
    project_title = sys.argv[3]
    path_to_output = sys.argv[4]


    scratch_temp_folder = tempfile.mkdtemp()
    pipe = subprocess.Popen(['/Applications/Scratch 1.4/Scratch.app/Contents/MacOS/Scratch', '-headless', path_to_scratch_image, 'filename', path_to_scratch_project, scratch_temp_folder])
    scratch_pid = pipe.pid

    elapsed_time = 0
    while not os.path.isfile(os.path.join(scratch_temp_folder, 'finished.txt')) and elapsed_time < 300:
        time.sleep(1)
        elapsed_time += 1

    subprocess.Popen(['kill', '-9', str(scratch_pid)])

    parseProject(project_title, scratch_temp_folder)

    shutil.make_archive(os.path.join(path_to_output, project_title), 'zip', TEMP_FOLDER)


if __name__ == '__main__':
    main()