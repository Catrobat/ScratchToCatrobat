import sys
import os
import shutil
import re
import tempfile
import hashlib
import Image
import xml.dom.minidom

TEMP_FOLDER = tempfile.mkdtemp()

def add_project(document, project_name):
    project = document.createElement("Content.Project")

    project_name_field = document.createElement("projectName")
    project_name_field.appendChild(document.createTextNode(project_name))

    device_name = document.createElement("deviceName")
    device_name.appendChild(document.createTextNode("Scratch"))

    android_version = document.createElement("androidVersion")
    android_version.appendChild(document.createTextNode("10"))

    catroid_version_code = document.createElement("catroidVersionCode")
    catroid_version_code.appendChild(document.createTextNode("820"))

    catroid_version_name = document.createElement("catroidVersionName")
    catroid_version_name.appendChild(document.createTextNode("0.6.0beta-820-debug"))
    
    screen_height = document.createElement("screenHeight")
    screen_height.appendChild(document.createTextNode("360"))
    
    screen_width = document.createElement("screenWidth")
    screen_width.appendChild(document.createTextNode("480"))
    
    sprite_list = document.createElement("spriteList")

    project.appendChild(project_name_field)
    project.appendChild(device_name)
    project.appendChild(android_version)
    project.appendChild(catroid_version_code)
    project.appendChild(catroid_version_name)
    project.appendChild(screen_height)
    project.appendChild(screen_width)
    project.appendChild(sprite_list)

    document.appendChild(project)

    return sprite_list

def parse_and_add_sprite(document, sprite_list, unparsed_sprite, project_path):
    sprite_node = document.createElement("Content.Sprite")
    sprite_list.appendChild(sprite_node)

    name_node = document.createElement("name")
    sprite_node.appendChild(name_node)
    
    costume_data_list_node = document.createElement("costumeDataList")
    sprite_node.appendChild(costume_data_list_node)
    
    sound_list_node = document.createElement("soundList")
    sprite_node.appendChild(sound_list_node)
    
    script_list_node = document.createElement("scriptList")
    sprite_node.appendChild(script_list_node)

    sprite_info, unparsed_bricks = unparsed_sprite.split("\n\n", 1)

    sprite_name, variables, lists, position, visibility, sounds, costumes = sprite_info.split('\n')

    name_node.appendChild(document.createTextNode(sprite_name))
    
    parse_and_add_costumes(document, costume_data_list_node, sprite_name, costumes, project_path)
    parse_and_add_sounds(document, sound_list_node, sprite_name, sounds, project_path)
    parse_and_add_scripts(document, script_list_node, unparsed_bricks)

    
def parse_and_add_costumes(document, costume_data_list_node, sprite_name, costumes, project_path):
    costumes = re.findall(r"'(.+?)'", costumes)
    costume_filenames = os.listdir(os.path.join(project_path, sprite_name, 'images'))
    for costume in costumes:
        for costume_filename in costume_filenames:
            if costume_filename.startswith(costume + '.'):
                filename = costume_filename
                break      

        Image.open(os.path.join(project_path, sprite_name, 'images', filename))\
             .save(os.path.join(TEMP_FOLDER, 'images', sprite_name + '_' + costume + '.png'))

        filename = sprite_name + '_' + costume + '.png'

        file_contents = open(os.path.join(TEMP_FOLDER, 'images', filename), 'rb').read()
        checksum = hashlib.md5(file_contents).hexdigest().upper()

        os.rename(os.path.join(TEMP_FOLDER, 'images', filename),\
                  os.path.join(TEMP_FOLDER, 'images', checksum + '_' + filename))
        filename = checksum + '_' + filename


        costume_data = document.createElement("Common.CostumeData")
        
        name_node = document.createElement("name")
        name_node.appendChild(document.createTextNode(costume))
        
        filename_node = document.createElement("fileName")
        filename_node.appendChild(document.createTextNode(filename))

        costume_data.appendChild(name_node)
        costume_data.appendChild(filename_node)

        costume_data_list_node.appendChild(costume_data)
        
    
def parse_and_add_sounds(document, sound_list_node, sprite_name, sounds, project_path):
    sounds = re.findall(r"'(.+?)'", sounds)
    sounds.remove('-')
    sounds.remove('record...')
    sounds_filenames = os.listdir(os.path.join(project_path, sprite_name, 'sounds'))
    for sound in sounds:
        for sound_filename in sounds_filenames:
            if sound_filename.startswith(sound + '.'):
                filename = sound_filename
                break      

        shutil.copy(os.path.join(project_path, sprite_name, 'sounds', filename),\
                    os.path.join(TEMP_FOLDER, 'sounds', sprite_name + '_' + sound_filename))

        filename = sprite_name + '_' + sound_filename

        file_contents = open(os.path.join(TEMP_FOLDER, 'sounds', filename), 'rb').read()
        checksum = hashlib.md5(file_contents).hexdigest().upper()

        os.rename(os.path.join(TEMP_FOLDER, 'sounds', filename),\
                  os.path.join(TEMP_FOLDER, 'sounds', checksum + '_' + filename))
        filename = checksum + '_' + filename

        sound_info = document.createElement("Common.SoundInfo")
        
        name_node = document.createElement("name")
        name_node.appendChild(document.createTextNode(sound))
        
        filename_node = document.createElement("fileName")
        filename_node.appendChild(document.createTextNode(filename))

        sound_info.appendChild(name_node)
        sound_info.appendChild(filename_node)

        sound_list_node.appendChild(sound_info)
    
def parse_and_add_scripts(document, script_list_node, unparsed_bricks):
    scripts_data = re.split(".*?EventHatMorph", unparsed_bricks)
    for script_data in scripts_data:
        if script_data:
            script_data = script_data.splitlines()
            if "'when I receive'" in script_data[0]:
                script_node = document.createElement("Content.BroadcastScript")
                action_node = document.createElement("receivedMessage")
                action_node.appendChild(document.createTextNode(script_data[1]))
                script_node.appendChild(action_node)

            elif "'when'" in script_data[0]:
                if script_data[1] == "Scratch-StartClicked":
                    script_node = document.createElement("Content.StartScript")
                    
                elif script_data[1] == "Scratch-MouseClickEvent":
                    script_node = document.createElement("Content.WhenScript")
                    action_node = document.createElement("action")
                    action_node.appendChild(document.createTextNode("Tapped"))
                    script_node.appendChild(action_node)
                elif script_data[1] == "Scratch-KeyPressedEvent":
                    continue #TODO

            brick_list_node = document.createElement("brickList")
            script_node.appendChild(brick_list_node)

            sprite_node = document.createElement("sprite")
            sprite_node.setAttribute("reference", "../../..")
            script_node.appendChild(sprite_node)

            script_list_node.appendChild(script_node)

            parse_and_add_bricks(document, brick_list_node, script_data[2:])



def parse_and_add_bricks(document, brick_list_node, script_data):
    while script_data:
        brick_name = script_data.pop(0)
        if "BlockMorph" in brick_name:
            brick_name = script_data.pop(0)
            if "'show'" in brick_name:
                brick_list_node.appendChild(get_brick_node(document, "Bricks.ShowBrick", {}))
            elif "'hide'" in brick_name:
                brick_list_node.appendChild(get_brick_node(document, "Bricks.HideBrick", {}))
            elif "broadcast %e" in brick_name:
                script_data.pop(0)
                message = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.BroadcastBrick", {"broadcastMessage": message}))
            elif "wait %n secs" in brick_name:
                script_data.pop(0)
                time = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                time = str(long(float(time) * 1000))
                brick_list_node.appendChild(get_brick_node(document, "Bricks.WaitBrick", {"timeToWaitInMilliSeconds": time}))
            elif "next costume" in brick_name:
                brick_list_node.appendChild(get_brick_node(document, "Bricks.NextCostumeBrick", {}))
            elif "set size to %n%" in brick_name:
                script_data.pop(0)
                size = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.SetSizeToBrick", {"size": size}))
            elif "change size by %n" in brick_name:
                script_data.pop(0)
                size = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.ChangeSizeByNBrick", {"size": size}))
            elif "go to x:%n y:%n" in brick_name:
                script_data.pop(0)
                x = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                y = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.PlaceAtBrick", {"xPosition": x, "yPosition": y}))
            elif "switch to costume %l" in brick_name:
                add_set_costume_brick(document, brick_list_node, script_data)
            elif "play sound %S" in brick_name:
                add_play_sound_brick(document, brick_list_node, script_data)
            elif "set %g effect to %n" in brick_name:
                script_data.pop(0)
                effect = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                script_data.pop(0)
                effect_value = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                if effect == 'brightness':
                    brick_list_node.appendChild(get_brick_node(document, "Bricks.SetBrightnessBrick", {"brightness": effect_value}))
                elif effect == 'ghost':
                    brick_list_node.appendChild(get_brick_node(document, "Bricks.SetGhostEffectBrick", {"transparency": effect_value}))
            elif "change %g effect to %n" in brick_name:
                script_data.pop(0)
                effect = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                script_data.pop(0)
                effect_value = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                if effect == 'brightness':
                    brick_list_node.appendChild(get_brick_node(document, "Bricks.ChangeBrightnessBrick", {"changeBrightness": effect_value}))
                elif effect == 'ghost':
                    brick_list_node.appendChild(get_brick_node(document, "Bricks.ChangeGhostEffectBrick", {"changeGhostEffect": effect_value}))
            elif "stop all sounds" in brick_name:
                brick_list_node.appendChild(get_brick_node(document, "Bricks.StopAllSoundsBrick", {}))
            elif "change volume by %n" in brick_name:
                script_data.pop(0)
                volume = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.ChangeVolumeByBrick", {"volume": volume}))
            elif "set volume to %n%" in brick_name:
                script_data.pop(0)
                volume = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.SetVolumeToBrick", {"volume": volume}))
            elif "say %s" in brick_name:
                script_data.pop(0)
                text = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.SpeakBrick", {"text": text}))
            elif "set x to" in brick_name:
                script_data.pop(0)
                x = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.SetXBrick", {"xPosition": x}))
            elif "set y to" in brick_name:
                script_data.pop(0)
                y = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.SetYBrick", {"yPosition": y}))
            elif "change x by" in brick_name:
                script_data.pop(0)
                x = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.ChangeXByBrick", {"xMovement": x}))
            elif "change y by" in brick_name:
                script_data.pop(0)
                y = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.ChangeYByBrick", {"yMovement": y}))
            elif "point in direction %d" in brick_name:
                script_data.pop(0)
                degrees = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.PointInDirectionBrick", {"degrees": degrees}))
            elif "glide %n secs to x:%n y:%n" in brick_name:
                script_data.pop(0)
                time = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                time = str(long(float(time) * 1000))
                x = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                y = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.GlideToBrick",
                                                    {"durationInMilliSeconds": time, "xDestination": x, "yDestination": y}))
            elif "if on edge, bounce" in brick_name:
                brick_list_node.appendChild(get_brick_node(document, "Bricks.IfOnEdgeBounceBrick", {}))
            elif "move %n steps" in brick_name:
                script_data.pop(0)
                steps = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.MoveNStepsBrick", {"steps": steps}))
            elif "go to front" in brick_name:
                brick_list_node.appendChild(get_brick_node(document, "Bricks.ComeToFrontBrick", {}))
            elif "go back %n layers" in brick_name:
                script_data.pop(0)
                steps = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                brick_list_node.appendChild(get_brick_node(document, "Bricks.GoNStepsBackBrick", {"steps": steps}))

def get_brick_node(document, brick_name, params):
    brick_node = document.createElement(brick_name)
    for key, value in params.items():
        broadcast_message_node = document.createElement(key)
        broadcast_message_node.appendChild(document.createTextNode(value))
        brick_node.appendChild(broadcast_message_node)
    sprite_node = document.createElement("sprite")
    sprite_node.setAttribute("reference", "../../../../..")
    brick_node.appendChild(sprite_node)
    return brick_node


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
            costume_date_node = document.createElement("costumeData")
            if index == 0:
                costume_date_node.setAttribute("reference", "../../../../../costumeDataList/Common.CostumeData")
            else:
                costume_date_node.setAttribute("reference", "../../../../../costumeDataList/Common.CostumeData[" + str(index) + "]")
            brick_node.appendChild(costume_date_node)
            break

def add_play_sound_brick(document, brick_list_node, script_data):
    script_data.pop(0)
    costume_name = re.findall(r"'(.+?)'", script_data.pop(0))[0]

    brick_node = document.createElement("Bricks.PlaySoundBrick")
    brick_list_node.appendChild(brick_node)
    
    sprite_node = document.createElement("sprite")
    sprite_node.setAttribute("reference", "../../../../..")
    brick_node.appendChild(sprite_node)

    costume_list_node = filter(lambda node: node.nodeName == "soundList", brick_list_node.parentNode.parentNode.parentNode.childNodes)[0]

    for index, costume_node in enumerate(costume_list_node.childNodes):
        costume_name_node = filter(lambda node: node.nodeName == "name", costume_node.childNodes)[0]
        if costume_name_node.firstChild.nodeValue == costume_name:
            costume_date_node = document.createElement("soundInfo")
            if index == 0:
                costume_date_node.setAttribute("reference", "../../../../../soundList/Common.SoundInfo")
            else:
                costume_date_node.setAttribute("reference", "../../../../../soundList/Common.SoundInfo[" + str(index) + "]")
            brick_node.appendChild(costume_date_node)
            break
 
def newwritexml(self, writer, indent='', addindent='', newl=''):
    if len(self.childNodes) == 1 and self.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE:
        writer.write(indent)
        self.oldwritexml(writer)
        writer.write(newl)
    else:
        self.oldwritexml(writer, indent, addindent, newl)

def main():
    if len(sys.argv) != 4:
        print 'Invalid arguments. Correct usage:'
        print 'python catrobatProjectBuilder.py <project_title> <path_to_project_folder> <ouput_file>'
        return 1
    project_name = sys.argv[1]
    project_path = sys.argv[2]
    output_file = sys.argv[3]

    xml.dom.minidom.Element.oldwritexml = xml.dom.minidom.Element.writexml
    xml.dom.minidom.Element.writexml = newwritexml

    os.makedirs(os.path.join(TEMP_FOLDER, 'images'))
    os.makedirs(os.path.join(TEMP_FOLDER, 'sounds'))

    project_data = open(os.path.join(project_path, 'blocks.txt'), 'U').read()
    unparsed_sprites = project_data.split("\n\n\n")

    document = xml.dom.minidom.Document()
    sprite_list = add_project(document, project_name)

    for unparsed_sprite in unparsed_sprites:
        if unparsed_sprite:
            parse_and_add_sprite(document, sprite_list, unparsed_sprite, project_path)
    
    projectcode_file = open(os.path.join(TEMP_FOLDER, 'projectcode.xml'), 'w')

    document.writexml(projectcode_file, addindent='  ', newl="\n")
    
    projectcode_file.close()

    shutil.copytree(TEMP_FOLDER, output_file)


if __name__ == '__main__':
    main()