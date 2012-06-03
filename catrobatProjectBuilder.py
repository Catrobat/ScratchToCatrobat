import sys
import os
import re
from xml.dom.minidom import Document

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
    
    parse_and_add_costumes(document, costume_data_list_node, costumes, project_path)
    parse_and_add_sounds(document, sound_list_node, sounds, project_path)
    parse_and_add_scripts(document, script_list_node, unparsed_bricks)

    
def parse_and_add_costumes(document, costume_data_list_node, costumes, project_path):
    costumes = re.findall(r"'(.+?)'", costumes)
    # TODO
    
def parse_and_add_sounds(document, sound_list_node, sounds, project_path):
    sounds = re.findall(r"'(.+?)'", sounds)
    # TODO
    
def parse_and_add_scripts(document, script_list_node, unparsed_bricks):
    pass
    # TODO

def main():
    if len(sys.argv) != 4:
        print 'Invalid arguments. Correct usage:'
        print 'python catrobatProjectBuilder.py <project_title> <path_to_project_folder> <ouput_file>'
        return 1
    project_name = sys.argv[1]
    project_path = sys.argv[2]

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