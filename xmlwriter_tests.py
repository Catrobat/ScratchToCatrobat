import unittest
import xml.dom.minidom
from xmlwriter import XmlWriter

class TestXmlWriter(unittest.TestCase):
    def setUp(self):
        self.xml_writer = XmlWriter()
        self.project_name = "Test Project Name"
        self.sprite_name = "SpriteName"

    def test_create_project(self):
        self.xml_writer.create_project(self.project_name)

        self.assertEquals(len(self.xml_writer.document.childNodes), 1)

        project_node = self.xml_writer.document.firstChild
        self.assertEquals(project_node.tagName, "Content.Project")
        self.assertEquals(len(project_node.childNodes), 8)

        self.assertEquals(len(project_node.getElementsByTagName("projectName")), 1)
        self.assertEquals(len(project_node.getElementsByTagName("deviceName")), 1)
        self.assertEquals(len(project_node.getElementsByTagName("androidVersion")), 1)
        self.assertEquals(len(project_node.getElementsByTagName("catroidVersionCode")), 1)
        self.assertEquals(len(project_node.getElementsByTagName("catroidVersionName")), 1)
        self.assertEquals(len(project_node.getElementsByTagName("screenHeight")), 1)
        self.assertEquals(len(project_node.getElementsByTagName("screenWidth")), 1)
        self.assertEquals(len(project_node.getElementsByTagName("spriteList")), 1)

        self.assertEquals(project_node.getElementsByTagName("projectName")[0].firstChild.nodeValue, self.project_name)
        self.assertEquals(project_node.getElementsByTagName("deviceName")[0].firstChild.nodeValue, "Scratch")
        self.assertEquals(project_node.getElementsByTagName("androidVersion")[0].firstChild.nodeValue, "10")
        self.assertEquals(project_node.getElementsByTagName("catroidVersionCode")[0].firstChild.nodeValue, "820")
        self.assertEquals(project_node.getElementsByTagName("catroidVersionName")[0].firstChild.nodeValue, "0.6.0beta-820-debug")
        self.assertEquals(project_node.getElementsByTagName("screenHeight")[0].firstChild.nodeValue, "360")
        self.assertEquals(project_node.getElementsByTagName("screenWidth")[0].firstChild.nodeValue, "480")
        self.assertFalse(project_node.getElementsByTagName("spriteList")[0].hasChildNodes())

    def test_add_sprite(self):
        sprite_name2 = "SpriteName2"

        self.xml_writer.create_project(self.project_name)
        sprite_list_node = self.xml_writer.document.firstChild.getElementsByTagName("spriteList")[0]
        
        self.xml_writer.add_sprite(self.sprite_name)
        self.assertEquals(len(sprite_list_node.childNodes), 1)
        first_sprite_node = sprite_list_node.firstChild

        self.assertEquals(first_sprite_node.tagName, "Content.Sprite")
        self.assertEquals(len(first_sprite_node.childNodes), 4)
        self.assertEquals(len(first_sprite_node.getElementsByTagName("name")), 1)
        self.assertEquals(len(first_sprite_node.getElementsByTagName("costumeDataList")), 1)
        self.assertEquals(len(first_sprite_node.getElementsByTagName("soundList")), 1)
        self.assertEquals(len(first_sprite_node.getElementsByTagName("scriptList")), 1)
        self.assertFalse(first_sprite_node.getElementsByTagName("costumeDataList")[0].hasChildNodes())
        self.assertFalse(first_sprite_node.getElementsByTagName("soundList")[0].hasChildNodes())
        self.assertFalse(first_sprite_node.getElementsByTagName("scriptList")[0].hasChildNodes())

        self.xml_writer.add_sprite(sprite_name2)
        self.assertEquals(len(sprite_list_node.childNodes), 2)
        second_sprite_node = sprite_list_node.lastChild

        self.assertEquals(first_sprite_node.getElementsByTagName("name")[0].firstChild.nodeValue, self.sprite_name)
        self.assertEquals(second_sprite_node.getElementsByTagName("name")[0].firstChild.nodeValue, sprite_name2)
        
        self.assertEquals(first_sprite_node, self.xml_writer.get_sprite_node(self.sprite_name))
        self.assertEquals(second_sprite_node, self.xml_writer.get_sprite_node(sprite_name2))

    def test_add_costume(self):
        costume_name = "CostumeName"
        costume_filename = "CostumeFilename"

        self.xml_writer.create_project(self.project_name)
        self.xml_writer.add_sprite(self.sprite_name)
        costume_list_node = self.xml_writer.get_sprite_node(self.sprite_name).getElementsByTagName("costumeDataList")[0]

        self.xml_writer.add_costume(costume_name, costume_filename, self.sprite_name)

        self.assertEquals(len(costume_list_node.childNodes), 1)
        costume_node = costume_list_node.firstChild

        self.assertEquals(costume_node.tagName, "Common.CostumeData")
        self.assertEquals(len(costume_node.childNodes), 2)
        self.assertEquals(len(costume_node.getElementsByTagName("name")), 1)
        self.assertEquals(len(costume_node.getElementsByTagName("fileName")), 1)

        self.assertEquals(costume_node.getElementsByTagName("name")[0].firstChild.nodeValue, costume_name)
        self.assertEquals(costume_node.getElementsByTagName("fileName")[0].firstChild.nodeValue, costume_filename)

    def test_add_sound(self):
        sound_name = "SoundName"
        sound_filename = "SOundFilename"

        self.xml_writer.create_project(self.project_name)
        self.xml_writer.add_sprite(self.sprite_name)
        sound_list_node = self.xml_writer.get_sprite_node(self.sprite_name).getElementsByTagName("soundList")[0]

        self.xml_writer.add_sound(sound_name, sound_filename, self.sprite_name)

        self.assertEquals(len(sound_list_node.childNodes), 1)
        sound_node = sound_list_node.firstChild

        self.assertEquals(sound_node.tagName, "Common.SoundInfo")
        self.assertEquals(len(sound_node.childNodes), 2)
        self.assertEquals(len(sound_node.getElementsByTagName("name")), 1)
        self.assertEquals(len(sound_node.getElementsByTagName("fileName")), 1)

        self.assertEquals(sound_node.getElementsByTagName("name")[0].firstChild.nodeValue, sound_name)
        self.assertEquals(sound_node.getElementsByTagName("fileName")[0].firstChild.nodeValue, sound_filename)

    def test_add_script(self):
        broadcasted_message = "BroadcastedMessage"

        self.xml_writer.create_project(self.project_name)
        self.xml_writer.add_sprite(self.sprite_name)
        script_list_node = self.xml_writer.get_sprite_node(self.sprite_name).getElementsByTagName("scriptList")[0]

        self.xml_writer.add_script(self.sprite_name, "BroadcastScript", [], broadcasted_message)
        self.assertEquals(len(script_list_node.childNodes), 1)
        broadcast_node = script_list_node.lastChild

        self.xml_writer.add_script(self.sprite_name, "StartScript", [])
        self.assertEquals(len(script_list_node.childNodes), 2)
        start_node = script_list_node.lastChild

        self.xml_writer.add_script(self.sprite_name, "WhenScript", [])
        self.assertEquals(len(script_list_node.childNodes), 3)
        when_node = script_list_node.lastChild

        self.assertEquals(broadcast_node.tagName, "Content.BroadcastScript")
        self.assertEquals(len(broadcast_node.childNodes), 3)
        self.assertEquals(len(broadcast_node.getElementsByTagName("receivedMessage")), 1)
        self.assertEquals(len(broadcast_node.getElementsByTagName("brickList")), 1)
        self.assertEquals(len(broadcast_node.getElementsByTagName("sprite")), 1)
        self.assertEquals(broadcast_node.getElementsByTagName("receivedMessage")[0].firstChild.nodeValue, broadcasted_message)
        self.assertFalse(broadcast_node.getElementsByTagName("sprite")[0].hasChildNodes())
        self.assertFalse(broadcast_node.getElementsByTagName("brickList")[0].hasChildNodes())

        self.assertEquals(start_node.tagName, "Content.StartScript")
        self.assertEquals(len(start_node.childNodes), 2)
        self.assertEquals(len(start_node.getElementsByTagName("brickList")), 1)
        self.assertEquals(len(start_node.getElementsByTagName("sprite")), 1)
        self.assertFalse(start_node.getElementsByTagName("sprite")[0].hasChildNodes())
        self.assertFalse(start_node.getElementsByTagName("brickList")[0].hasChildNodes())

        self.assertEquals(when_node.tagName, "Content.WhenScript")
        self.assertEquals(len(when_node.childNodes), 3)
        self.assertEquals(len(when_node.getElementsByTagName("action")), 1)
        self.assertEquals(len(when_node.getElementsByTagName("brickList")), 1)
        self.assertEquals(len(when_node.getElementsByTagName("sprite")), 1)

        self.assertEquals(when_node.getElementsByTagName("action")[0].firstChild.nodeValue, "Tapped")
        self.assertFalse(when_node.getElementsByTagName("sprite")[0].hasChildNodes())
        self.assertFalse(when_node.getElementsByTagName("brickList")[0].hasChildNodes())

    def test_add_brick(self):
        brick_name1 = "BrickName1"
        brick_param1 = "BrickParameter1"
        brick_value1 = "BrickValue1"
        brick_name2 = "BrickName2"
        brick_param2 = "BrickParameter2"
        brick_value2 = "BrickValue2"
        brick_param3 = "BrickParameter3"
        brick_value3 = "BrickValue3"

        self.xml_writer.create_project(self.project_name)
        self.xml_writer.add_sprite(self.sprite_name)
        self.xml_writer.add_script(self.sprite_name, "StartScript", [(brick_name1, {brick_param1: brick_value1}),\
                                                                    (brick_name2, {brick_param2: brick_value2, brick_param3: brick_value3})])

        brick_list_node = self.xml_writer.get_sprite_node(self.sprite_name).getElementsByTagName("scriptList")[0].getElementsByTagName("brickList")[0]
        self.assertEquals(len(brick_list_node.childNodes), 2)

        brick1_node = brick_list_node.firstChild
        brick2_node = brick_list_node.lastChild

        self.assertEquals(brick1_node.tagName, brick_name1)
        self.assertEquals(len(brick1_node.childNodes), 2)
        self.assertEquals(len(brick1_node.getElementsByTagName(brick_param1)), 1)
        self.assertEquals(len(brick1_node.getElementsByTagName("sprite")), 1)

        self.assertEquals(brick1_node.getElementsByTagName(brick_param1)[0].firstChild.nodeValue, brick_value1)
        self.assertFalse(brick1_node.getElementsByTagName("sprite")[0].hasChildNodes())

        self.assertEquals(brick2_node.tagName, brick_name2)
        self.assertEquals(len(brick2_node.childNodes), 3)
        self.assertEquals(len(brick2_node.getElementsByTagName(brick_param2)), 1)
        self.assertEquals(len(brick2_node.getElementsByTagName(brick_param3)), 1)
        self.assertEquals(len(brick2_node.getElementsByTagName("sprite")), 1)

        self.assertEquals(brick2_node.getElementsByTagName(brick_param2)[0].firstChild.nodeValue, brick_value2)
        self.assertEquals(brick2_node.getElementsByTagName(brick_param3)[0].firstChild.nodeValue, brick_value3)
        self.assertFalse(brick2_node.getElementsByTagName("sprite")[0].hasChildNodes())