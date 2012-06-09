import sys
import os
import shutil
import re
import tempfile
import hashlib
import Image
from xml.dom.minidom import Document

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
    screen_height.appendChild(document.createTextNode("480"))
    
    screen_width = document.createElement("screenWidth")
    screen_width.appendChild(document.createTextNode("360"))
    
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
    
    costume_data_list_node = document.createElement("costumeDataList")
    sprite_node.appendChild(costume_data_list_node)

    name_node = document.createElement("name")
    sprite_node.appendChild(name_node)
    
    script_list_node = document.createElement("scriptList")
    sprite_node.appendChild(script_list_node)
    
    sound_list_node = document.createElement("soundList")
    sprite_node.appendChild(sound_list_node)

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

            brick_list = document.createElement("brickList")
            script_node.appendChild(brick_list)

            sprite_node = document.createElement("sprite")
            sprite_node.setAttribute("reference", "../../..")
            script_node.appendChild(sprite_node)

            script_list_node.appendChild(script_node)


def main():
    if len(sys.argv) != 4:
        print 'Invalid arguments. Correct usage:'
        print 'python catrobatProjectBuilder.py <project_title> <path_to_project_folder> <ouput_file>'
        return 1
    project_name = sys.argv[1]
    project_path = sys.argv[2]

    os.makedirs(os.path.join(TEMP_FOLDER, 'images'))
    os.makedirs(os.path.join(TEMP_FOLDER, 'sounds'))

    project_data = open(os.path.join(project_path, 'blocks.txt'), 'U').read()
    unparsed_sprites = project_data.split("\n\n\n")

    document = Document()
    sprite_list = add_project(document, project_name)

    for unparsed_sprite in unparsed_sprites:
        if unparsed_sprite:
            parse_and_add_sprite(document, sprite_list, unparsed_sprite, project_path)
    
    print document.toprettyxml(indent="  ")


if __name__ == '__main__':
    main()