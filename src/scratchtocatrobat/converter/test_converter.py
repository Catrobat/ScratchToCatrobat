#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2017 The Catrobat Team
#  (http://developer.catrobat.org/credits)
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
#  along with this program.  If not, see http://www.gnu.org/licenses/.
import os
import unittest
import re
import colorsys
from threading import Lock

import org.catrobat.catroid.common as catcommon
import org.catrobat.catroid.content as catbase
from org.catrobat.catroid.ui.fragment import SpriteFactory
import org.catrobat.catroid.content.bricks as catbricks
import org.catrobat.catroid.content.bricks.Brick as catbasebrick
import org.catrobat.catroid.formulaeditor as catformula
import org.catrobat.catroid.formulaeditor.FormulaElement.ElementType as catElementType
import xml.etree.cElementTree as ET

from scratchtocatrobat.converter import catrobat, converter, mediaconverter
from scratchtocatrobat.converter.converter import Converter
from scratchtocatrobat.tools import common, common_testing, svgtopng, wavconverter
from scratchtocatrobat.scratch import scratch, scratch3

BACKGROUND_LOCALIZED_GERMAN_NAME = "Hintergrund"
BACKGROUND_ORIGINAL_NAME = "Stage"
ns_registry_lock = Lock()


def create_catrobat_sprite_stub(name=None):
    sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, "Dummy" if name is None else name)
    looks = sprite.getLookList()
    for lookname in ["look1", "look2", "look3"]:
        looks.add(catrobat.create_lookdata(lookname, None))
    return sprite

def create_catrobat_background_sprite_stub():
    sprite_stub = create_catrobat_sprite_stub(catrobat._BACKGROUND_SPRITE_NAME)
    catrobat.set_as_background(sprite_stub)
    return sprite_stub

DUMMY_CATR_SPRITE = create_catrobat_sprite_stub()
TEST_PROJECT_PATH = common_testing.get_test_project_path("dancing_castle")


def _dummy_project():
    return scratch.Project(TEST_PROJECT_PATH, name="dummy")

# TODO: fix / reorganize test
#
# class TestConvertExampleProject(common_testing.ProjectTestCase):
#
#     expected_sprite_names = ["Sprite1, Cassy Dance"]
#     expected_script_classes = [[catbase.StartScript, ], []]
#     expected_brick_classes = [[catbricks.WaitBrick, catbricks.RepeatBrick, catbricks.MoveNStepsBrick, catbricks.WaitBrick, catbricks.MoveNStepsBrick, catbricks.WaitBrick, catbricks.LoopEndBrick], []]
#
#     def __init__(self, *args, **kwargs):
#         super(TestConvertExampleProject, self).__init__(*args, **kwargs)
#
#     def setUp(self):
#         super(TestConvertExampleProject, self).setUp()
#         self.project = scratch.Project(TEST_PROJECT_PATH, name="dummy")
#
#     def test_can_convert_to_catrobat_structure_including_svg_to_png(self):
#         count_svg_and_png_files = 0
#         for md5_name in self.project.md5_to_resource_path_map:
#             common.log.info(md5_name)
#             if os.path.splitext(md5_name)[1] in {".png", ".svg"}:
#                 count_svg_and_png_files += 1
#
#         converter.save_as_catrobat_program_to(self.project, self.temp_dir)
#
#         images_dir = converter.images_dir_of_project(self.temp_dir)
#         assert os.path.exists(images_dir)
#         sounds_dir = converter.sounds_dir_of_project(self.temp_dir)
#         assert os.path.exists(sounds_dir)
#         code_xml_path = os.path.join(self.temp_dir, catrobat.PROGRAM_SOURCE_FILE_NAME)
#         assert os.path.exists(code_xml_path)
#         assert not glob.glob(os.path.join(images_dir, "*.svg")), "Unsupported svg files are in Catrobat folder."
#
#         self.assertValidCatrobatProgramStructure(self.temp_dir, self.project.name)
#         actual_count = len(glob.glob(os.path.join(images_dir, "*.png")))
#         assert actual_count - len(self.project.listened_keys) == count_svg_and_png_files
#
#     def test_can_get_catrobat_resource_file_name_of_scratch_resources(self):
#         resource_names_scratch_to_catrobat_map = {
#             "83a9787d4cb6f3b7632b4ddfebf74367.wav": ["83a9787d4cb6f3b7632b4ddfebf74367_pop.wav"] * 2,
#             "510da64cf172d53750dffd23fbf73563.png": ["510da64cf172d53750dffd23fbf73563_backdrop1.png"],
#             "033f926829a446a28970f59302b0572d.png": ["033f926829a446a28970f59302b0572d_castle1.png"],
#             "83c36d806dc92327b9e7049a565c6bff.wav": ["83c36d806dc92327b9e7049a565c6bff_meow.wav"]}
#         for resource_name in resource_names_scratch_to_catrobat_map:
#             expected = resource_names_scratch_to_catrobat_map[resource_name]
#             assert converter._catrobat_resource_file_name_for(resource_name, self.project) == expected
#
#     def test_can_convert_scratch_project_to_catrobat_zip(self):
#         catrobat_zip_file_name = converter.save_as_catrobat_program_package_to(self.project, self.temp_dir)
#
#         self.assertValidCatrobatProgramPackageAndUnpackIf(catrobat_zip_file_name, self.project.name)
#
#     def test_can_convert_scratch_project_with_utf8_characters_catrobat_zip(self):
#         project = scratch.Project(common_testing.get_test_project_path("utf_encoding"))
#         catrobat_zip_file_name = converter.save_as_catrobat_program_package_to(project, self._testresult_folder_path)
#
#         self.assertValidCatrobatProgramPackageAndUnpackIf(catrobat_zip_file_name, project.name)
#
#     def test_can_convert_complete_project_to_catrobat_project_class(self):
#         _catr_project = converter.catrobat_program_from(self.project)
#         assert isinstance(_catr_project, catbase.Project)
#
#         assert _catr_project.getXmlHeader().virtualScreenHeight == scratch.STAGE_HEIGHT_IN_PIXELS
#         assert _catr_project.getXmlHeader().virtualScreenWidth == scratch.STAGE_WIDTH_IN_PIXELS
#
#         catr_sprites = _catr_project.getSpriteList()
#         assert catr_sprites
#         assert all(isinstance(_, catbase.Sprite) for _ in catr_sprites)
#         assert catr_sprites[0].getName() == catrobat.BACKGROUND_SPRITE_NAME
#
#     def test_can_convert_object_to_catrobat_sprite_class(self):
#         sprites = [converter._catrobat_sprite_from(scratchobj) for scratchobj in self.project.objects]
#         assert all(isinstance(_, catbase.Sprite) for _ in sprites)
#
#         sprite_0 = sprites[0]
#         assert sprite_0.getName() == scratch.STAGE_OBJECT_NAME
#         assert [_.__class__ for _ in sprite_0.scriptList] == [catbase.StartScript]
#         start_script = sprite_0.scriptList[0]
#         # TODO into own test case
#         set_look_brick = start_script.getBrick(0)
#         assert isinstance(set_look_brick, catbricks.SetLookBrick), "Mismatch to Scratch behavior: Implicit SetLookBrick is missing"
#
#         sprite0_looks = sprite_0.getLookDataList()
#         assert sprite0_looks
#         assert all(isinstance(look, catcommon.LookData) for look in sprite0_looks)
#         sprite0_sounds = sprite_0.getSoundList()
#         assert sprite0_sounds
#         assert all(isinstance(sound, catcommon.SoundInfo) for sound in sprite0_sounds)
#
#         sprite_1 = sprites[1]
#         assert sprite_1.getName() == "Sprite1"
#         assert [_.__class__ for _ in sprite_1.scriptList] == [catbase.StartScript, catbase.BroadcastScript]
#
#         start_script = sprite_1.scriptList[0]
#         # TODO into own test case
#         place_at_brick = start_script.getBrick(1)
#         assert isinstance(place_at_brick, catbricks.PlaceAtBrick), "Mismatch to Scratch behavior: Implicit PlaceAtBrick is missing"
#         assert place_at_brick.xPosition.formulaTree.type == catformula.FormulaElement.ElementType.NUMBER
#         assert place_at_brick.xPosition.formulaTree.value == str(self.project.objects[1].get_scratchX())
#         assert place_at_brick.yPosition.formulaTree.type == catformula.FormulaElement.ElementType.OPERATOR
#         assert place_at_brick.yPosition.formulaTree.value == "MINUS"
#         assert place_at_brick.yPosition.formulaTree.rightChild.type == catformula.FormulaElement.ElementType.NUMBER
#         assert place_at_brick.yPosition.formulaTree.rightChild.value == str(-self.project.objects[1].get_scratchY())
#         # TODO: test for implicit bricks
#
#         sprite1_looks = sprite_1.getLookDataList()
#         assert sprite1_looks
#         assert all(isinstance(_, catcommon.LookData) for _ in sprite1_looks)
#         sprite1_sounds = sprite_1.getSoundList()
#         assert sprite1_sounds
#         assert all(isinstance(_, catcommon.SoundInfo) for _ in sprite1_sounds)
#
#         sprite_2 = sprites[2]
#         assert sprite_2.getName() == "Cassy Dance"
#         assert [_.__class__ for _ in sprite_2.scriptList] == [catbase.StartScript]
#         sprite2_looks = sprite_2.getLookDataList()
#         assert sprite2_looks
#         assert all(isinstance(_, catcommon.LookData) for _ in sprite2_looks)
#
#     def test_can_convert_script_to_catrobat_script_class(self):
#         scratch_script = self.project.objects[1].scripts[0]
#         catr_script = converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE, self.test_project)
#         assert catr_script
#         expected_script_class = [catbase.StartScript]
#         expected_brick_classes = [catbricks.WaitBrick, catbricks.NoteBrick, catbricks.RepeatBrick, catbricks.MoveNStepsBrick, catbricks.WaitBrick, catbricks.NoteBrick, catbricks.MoveNStepsBrick, catbricks.WaitBrick, catbricks.NoteBrick, catbricks.LoopEndBrick]
#         self.assertScriptClasses(expected_script_class, expected_brick_classes, catr_script)
#
#     def test_can_convert_costume_to_catrobat_lookdata_class(self):
#         costumes = self.project.objects[1].get_costumes()
#         for (expected_name, expected_file_name), costume in zip([("costume1", "f9a1c175dbe2e5dee472858dd30d16bb_costume1.svg"), ("costume2", "6e8bd9ae68fdb02b7e1e3df656a75635_costume2.svg")], costumes):
#             look = converter._catrobat_look_from(costume)
#             assert isinstance(look, catcommon.LookData)
#             assert look.getName() == expected_name
#             assert look.getLookFileName() == expected_file_name
#
#     def test_can_convert_sound_to_catrobat_soundinfo_class(self):
#         sounds = self.project.objects[1].get_sounds()
#         for (expected_name, expected_file_name), sound in zip([("meow", "83c36d806dc92327b9e7049a565c6bff_meow.wav"), ], sounds):
#             soundinfo = converter._catrobat_sound_from(sound)
#             assert isinstance(soundinfo, catcommon.SoundInfo)
#             assert soundinfo.getTitle() == expected_name
#             assert soundinfo.getSoundFileName() == expected_file_name


# def ConverterTestClass(class_):
#     class Wrapper:
#         def __init__(self, *args, **kwargs):
#             _dummy_project = catbase.Project(None, "__test_project__")
#             self.block_converter = converter._ScratchObjectConverter(_dummy_project, None)
#             class_(*args, **kwargs)
#     return Wrapper

class TestConvertBlocks(common_testing.BaseTestCase):

    def setUp(self):
        super(TestConvertBlocks, self).setUp()
        self.test_project = catbase.Project(None, "__test_project__")
        self.test_scene = catbase.Scene("Scene 1", self.test_project)
        self.test_project.sceneList.add(self.test_scene)
        self._name_of_test_list = "my_test_list"
        self.block_converter = converter._ScratchObjectConverter(self.test_project, None)
        # create and add user list for user list bricks to project
        list_to_add = catformula.UserList(self._name_of_test_list)
        self.block_converter._catrobat_project.userLists.add(list_to_add)

        # create dummy sprite
        self.sprite_stub = create_catrobat_background_sprite_stub()

    def get_sprite_with_soundinfo(self, soundinfo_name):
        dummy_sound = catcommon.SoundInfo()
        dummy_sound.setName(soundinfo_name)
        dummy_sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, "TestDummy")
        dummy_sprite.getSoundList().add(dummy_sound)
        return dummy_sprite

    ###############################################################################################################
    #
    # Script block tests
    #
    ###############################################################################################################

    # whenIReceive
    def test_can_convert_broadcast_script(self):
        broadcast_message = "space"
        scratch_script = scratch.Script([30, 355, [["whenIReceive", broadcast_message], ["changeGraphicEffect:by:", "color", 25]]])
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE, self.test_project)
        self.assertTrue(isinstance(catr_script, catbase.BroadcastScript))
        self.assertEqual(broadcast_message, catr_script.getBroadcastMessage())

    # whenIReceive
    def test_can_convert_broadcast_script_by_ignoring_case_sensitive_broadcast_message(self):
        broadcast_message = "hElLo WOrLD" # mixed case letters...
        scratch_script = scratch.Script([30, 355, [["whenIReceive", broadcast_message], ["changeGraphicEffect:by:", "color", 25]]])
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE, self.test_project)
        self.assertTrue(isinstance(catr_script, catbase.BroadcastScript))
        self.assertNotEqual(catr_script.getBroadcastMessage(), broadcast_message)
        self.assertEqual(catr_script.getBroadcastMessage(), broadcast_message.lower())

    # whenKeyPressed
    def test_can_convert_keypressed_script(self):
        scratch_script = scratch.Script([30, 355, [["whenKeyPressed", "space"], ["changeGraphicEffect:by:", "color", 25]]])
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE, self.test_project)
        # KeyPressed-scripts are represented with broadcast-scripts with a special key-message
        self.assertTrue(isinstance(catr_script, catbase.BroadcastScript))
        self.assertEqual(converter._key_to_broadcast_message("space"), catr_script.getBroadcastMessage())

    # whenClicked
    def test_can_convert_whenclicked_script(self):
        scratch_script = scratch.Script([30, 355, [["whenClicked"], ["changeGraphicEffect:by:", "color", 25]]])
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE, self.test_project)
        self.assertTrue(isinstance(catr_script, catbase.WhenScript))

    #whenSensorGreaterThan
    def test_can_convert_when_loudness_greater_than_script_with_formula(self):
        scratch_script= scratch.Script([30, 355, [["whenSensorGreaterThan", "loudness", ["+", 2, 1]], ["say:", "Hello!"]]])
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE, self.test_project)

        assert isinstance(catr_script, catbase.WhenConditionScript)
        formula = catr_script.formulaMap[catbricks.Brick.BrickField.IF_CONDITION] #@UndefinedVariable
        assert isinstance(formula, catformula.Formula)

        assert formula.formulaTree.value == str(catformula.Operators.GREATER_THAN)
        assert formula.formulaTree.leftChild.value == str(catformula.Sensors.LOUDNESS)
        assert formula.formulaTree.rightChild.value == str(catformula.Operators.PLUS)
        assert formula.formulaTree.rightChild.leftChild.value == "2"
        assert formula.formulaTree.rightChild.rightChild.value == "1"

    #whenSensorGreaterThan
    def test_can_convert_when_timer_greater_than_script_with_formula(self):
        raw_json = {
            "objName": "Stage",
            "currentCostumeIndex": 0,
            "penLayerMD5": "5c81a336fab8be57adc039a8a2b33ca9.png",
            "penLayerID": 0,
            "tempoBPM": 60,
            "children": [{
                "objName": "Sprite1",
                "scripts": [[72, 132, [["whenSensorGreaterThan", "timer", ["+", 2, 1]], ["say:", "Hello!"]]]],
                "currentCostumeIndex": 0,
                "indexInLibrary": 1,
                "spriteInfo": {}
            }],
            "info": {}
        }

        raw_project = scratch.RawProject(raw_json)
        workaround_info = raw_project.objects[1].preprocess_object([raw_project.objects[0].name, raw_project.objects[1].name])
        assert workaround_info[scratch.ADD_TIMER_SCRIPT_KEY] == True
        timer_background_workaround = [['whenGreenFlag'], ['doForever', \
                                                           [['changeVar:by:', scratch.S2CC_TIMER_VARIABLE_NAME, scratch.UPDATE_HELPER_VARIABLE_TIMEOUT],
                                                            ['wait:elapsed:from:', scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]]]]
        assert raw_project.objects[0].scripts[0].raw_script == timer_background_workaround

        catr_script = self.block_converter._catrobat_script_from(raw_project.objects[1].scripts[0], DUMMY_CATR_SPRITE, self.test_project)

        assert isinstance(catr_script, catbase.WhenConditionScript)
        formula = catr_script.formulaMap[catbricks.Brick.BrickField.IF_CONDITION] #@UndefinedVariable
        assert isinstance(formula, catformula.Formula)

        assert formula.formulaTree.value == str(catformula.Operators.GREATER_THAN)
        assert formula.formulaTree.leftChild.value == scratch.S2CC_TIMER_VARIABLE_NAME
        assert formula.formulaTree.rightChild.value == str(catformula.Operators.PLUS)
        assert formula.formulaTree.rightChild.leftChild.value == "2"
        assert formula.formulaTree.rightChild.rightChild.value == "1"

    #whenBackgroundSwitchesTo
    def test_can_convert_when_background_switches_to_script_for_sprite(self):
        scratch_script= scratch.Script([321, 89, [["whenSceneStarts", "look1"], ["say:", "Hello!"]]])
        self.test_project.getDefaultScene().spriteList.add(self.sprite_stub)
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE, self.test_project)
        assert isinstance(catr_script, catbase.WhenBackgroundChangesScript)
        assert catr_script.getLook().getName() == "look1"
        assert catr_script.getLook() == self.sprite_stub.getLookList()[0]
        assert len(catr_script.getBrickList()) == 1
        assert isinstance(catr_script.getBrickList()[0], catbricks.SayBubbleBrick)

    #whenBackgroundSwitchesTo
    def test_can_convert_when_background_switches_to_script_for_background(self):
        raw_json = {
            "objName": "Stage",
            "scripts": [[47, 97, [["whenSceneStarts", "look1"]]]],
            "costumes": [{
                "costumeName": "backdrop1",
                "baseLayerID": 3,
                "baseLayerMD5": "739b5e2a2435f6e1ec2993791b423146.png",
                "bitmapResolution": 1,
                "rotationCenterX": 240,
                "rotationCenterY": 180
            }],
            "children": [],
            "currentCostumeIndex": 0,
            "penLayerMD5": "5c81a336fab8be57adc039a8a2b33ca9.png",
            "penLayerID": 0,
            "tempoBPM": 60,
            "info": {}
        }

        raw_project = scratch.RawProject(raw_json)
        self.test_project.getDefaultScene().spriteList.add(self.sprite_stub)
        catr_script = self.block_converter._catrobat_script_from(raw_project.objects[0].scripts[0], DUMMY_CATR_SPRITE, self.test_project)
        assert isinstance(catr_script, catbase.WhenBackgroundChangesScript)
        assert catr_script.getLook().name == "look1"
        assert catr_script.getLook() == self.sprite_stub.getLookList()[0]
        assert len(catr_script.getBrickList()) == 0

    #whenBackgroundSwitchesTo
    def test_fail_convert_when_background_switches_to_script(self):
        scratch_script= scratch.Script([321, 89, [["whenSceneStarts", "look1"], ["say:", "Hello!"]]])
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE, self.test_project)
        assert isinstance(catr_script, catbase.StartScript)

    #whenSensorGreaterThan
    def test_can_convert_when_video_motion_greater_than_script_with_formula(self):
        scratch_script= scratch.Script([30, 355, [["whenSensorGreaterThan", "video motion", ["+", 2, 1]], ["say:", "Hello!"]]])
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE, self.test_project)
        assert isinstance(catr_script, catbase.StartScript)

    ###############################################################################################################
    #
    # Formula element block tests (compute, operator, ...)
    #
    ###############################################################################################################

    #--------------------------------------------------------------------------------------------------------------
    # user list formula tests
    #--------------------------------------------------------------------------------------------------------------

    # getLine:ofList:
    def test_can_convert_get_line_str_index_of_list_block(self):
        index = "1"
        scratch_block = ["getLine:ofList:", index, self._name_of_test_list]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.LIST_ITEM.toString() # @UndefinedVariable
        index_formula_element = catr_formula_element.leftChild
        user_list_formula_element = catr_formula_element.rightChild
        assert user_list_formula_element.type == catformula.FormulaElement.ElementType.USER_LIST
        assert user_list_formula_element.value == self._name_of_test_list
        assert index_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert index_formula_element.value == index

    # getLine:ofList:
    def test_can_convert_get_line_numeric_index_of_list_block(self):
        index = 1
        scratch_block = ["getLine:ofList:", index, self._name_of_test_list]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.LIST_ITEM.toString() # @UndefinedVariable
        index_formula_element = catr_formula_element.leftChild
        user_list_formula_element = catr_formula_element.rightChild
        assert user_list_formula_element.type == catformula.FormulaElement.ElementType.USER_LIST
        assert user_list_formula_element.value == self._name_of_test_list
        assert index_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert index_formula_element.value == str(index)

    # getLine:ofList:
    def test_can_convert_get_last_line_of_list_block(self):
        scratch_block = ["getLine:ofList:", "last", self._name_of_test_list]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.LIST_ITEM.toString() # @UndefinedVariable
        last_index_formula_element = catr_formula_element.leftChild
        user_list_formula_element = catr_formula_element.rightChild
        assert user_list_formula_element.type == catformula.FormulaElement.ElementType.USER_LIST
        assert user_list_formula_element.value == self._name_of_test_list

        assert last_index_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert last_index_formula_element.value == catformula.Functions.NUMBER_OF_ITEMS.toString() # @UndefinedVariable
        assert last_index_formula_element.rightChild == None
        inner_user_list_formula_element = last_index_formula_element.leftChild
        assert inner_user_list_formula_element.type == catformula.FormulaElement.ElementType.USER_LIST
        assert inner_user_list_formula_element.value == self._name_of_test_list
        assert inner_user_list_formula_element.leftChild == None
        assert inner_user_list_formula_element.rightChild == None

    # getLine:ofList:
    def test_can_convert_get_random_line_of_list_block(self):
        scratch_block = ["getLine:ofList:", "random", self._name_of_test_list]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.LIST_ITEM.toString() # @UndefinedVariable
        random_index_formula_element = catr_formula_element.leftChild
        user_list_formula_element = catr_formula_element.rightChild
        assert user_list_formula_element.type == catformula.FormulaElement.ElementType.USER_LIST
        assert user_list_formula_element.value == self._name_of_test_list

        assert random_index_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert random_index_formula_element.value == catformula.Functions.RAND.toString() # @UndefinedVariable
        start_formula_element = random_index_formula_element.leftChild
        assert start_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert start_formula_element.value == "1"

        last_index_formula_element = random_index_formula_element.rightChild
        assert last_index_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert last_index_formula_element.value == catformula.Functions.NUMBER_OF_ITEMS.toString() # @UndefinedVariable
        assert last_index_formula_element.rightChild == None
        inner_user_list_formula_element = last_index_formula_element.leftChild
        assert inner_user_list_formula_element.type == catformula.FormulaElement.ElementType.USER_LIST
        assert inner_user_list_formula_element.value == self._name_of_test_list
        assert inner_user_list_formula_element.leftChild == None
        assert inner_user_list_formula_element.rightChild == None

    # computeFunction:of:, floor
    def test_can_convert_floor_block(self):
        value = 9.6
        scratch_block = ["computeFunction:of:", "floor", value]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.FLOOR.toString() # @UndefinedVariable
        value_formula_element = catr_formula_element.leftChild
        assert catr_formula_element.rightChild == None
        assert value_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert value_formula_element.value == str(value)

    # computeFunction:of:, ceiling
    def test_can_convert_ceiling_block(self):
        value = 9.6
        scratch_block = ["computeFunction:of:", "ceiling", value]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.CEIL.toString() # @UndefinedVariable
        value_formula_element = catr_formula_element.leftChild
        assert catr_formula_element.rightChild == None
        assert value_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert value_formula_element.value == str(value)

    # 10 ^
    def test_can_convert_pow_of_10_block(self):
        exponent = 6
        scratch_block = ["10 ^", exponent]
        [formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        self.assertIsInstance(formula_element, catformula.FormulaElement)
        self.assertEqual(formula_element.type, catformula.FormulaElement.ElementType.FUNCTION)
        self.assertEqual(formula_element.value, catformula.Functions.POWER.toString())

        base_fe = formula_element.leftChild
        self.assertIsInstance(base_fe, catformula.FormulaElement)
        self.assertEqual(base_fe.type, catformula.FormulaElement.ElementType.NUMBER)
        self.assertEqual(base_fe.value, str(10))
        self.assertIsNone(base_fe.leftChild)
        self.assertIsNone(base_fe.rightChild)

        exponent_fe = formula_element.rightChild
        self.assertIsInstance(exponent_fe, catformula.FormulaElement)
        self.assertEqual(exponent_fe.type, catformula.FormulaElement.ElementType.NUMBER)
        self.assertEqual(exponent_fe.value, str(exponent))
        self.assertIsNone(exponent_fe.leftChild)
        self.assertIsNone(exponent_fe.rightChild)

    # lineCountOfList:
    def test_can_convert_line_count_of_list_block(self):
        scratch_block = ["lineCountOfList:", self._name_of_test_list]
        [last_index_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(last_index_formula_element, catformula.FormulaElement)
        assert last_index_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert last_index_formula_element.value == catformula.Functions.NUMBER_OF_ITEMS.toString() # @UndefinedVariable
        assert last_index_formula_element.rightChild == None
        inner_user_list_formula_element = last_index_formula_element.leftChild
        assert inner_user_list_formula_element.type == catformula.FormulaElement.ElementType.USER_LIST
        assert inner_user_list_formula_element.value == self._name_of_test_list
        assert inner_user_list_formula_element.leftChild == None
        assert inner_user_list_formula_element.rightChild == None

    # list:contains:
    def test_can_convert_list_contains_number_block(self):
        value = "1.23"
        scratch_block = ["list:contains:", self._name_of_test_list, value]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)

        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.CONTAINS.toString() # @UndefinedVariable

        inner_user_list_formula_element = catr_formula_element.leftChild
        assert inner_user_list_formula_element.type == catformula.FormulaElement.ElementType.USER_LIST
        assert inner_user_list_formula_element.value == self._name_of_test_list
        assert inner_user_list_formula_element.leftChild == None
        assert inner_user_list_formula_element.rightChild == None

        value_formula_element = catr_formula_element.rightChild
        assert value_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert value_formula_element.value == value
        assert value_formula_element.leftChild == None
        assert value_formula_element.rightChild == None

    # list:contains:
    def test_can_convert_list_contains_string_block(self):
        value = "dummyString"
        scratch_block = ["list:contains:", self._name_of_test_list, value]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)

        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.CONTAINS.toString() # @UndefinedVariable

        inner_user_list_formula_element = catr_formula_element.leftChild
        assert inner_user_list_formula_element.type == catformula.FormulaElement.ElementType.USER_LIST
        assert inner_user_list_formula_element.value == self._name_of_test_list
        assert inner_user_list_formula_element.leftChild == None
        assert inner_user_list_formula_element.rightChild == None

        value_formula_element = catr_formula_element.rightChild
        assert value_formula_element.type == catformula.FormulaElement.ElementType.STRING
        assert value_formula_element.value == value
        assert value_formula_element.leftChild == None
        assert value_formula_element.rightChild == None

    #--------------------------------------------------------------------------------------------------------------
    # string formula tests
    #--------------------------------------------------------------------------------------------------------------

    # stringLength:
    def test_can_convert_string_length_block_with_string(self):
        value = "dummyString"
        scratch_block = ["stringLength:", value]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)

        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.LENGTH.toString() # @UndefinedVariable
        assert catr_formula_element.rightChild == None

        value_formula_element = catr_formula_element.leftChild
        assert value_formula_element.type == catformula.FormulaElement.ElementType.STRING
        assert value_formula_element.value == value
        assert value_formula_element.leftChild == None
        assert value_formula_element.rightChild == None

    # stringLength:
    def test_can_convert_string_length_block_with_number(self):
        value = 31.12
        scratch_block = ["stringLength:", value]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)

        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.LENGTH.toString() # @UndefinedVariable
        assert catr_formula_element.rightChild == None

        value_formula_element = catr_formula_element.leftChild
        assert value_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert value_formula_element.value == str(value)
        assert value_formula_element.leftChild == None
        assert value_formula_element.rightChild == None

    # letter:of:
    def test_can_convert_letter_of_number_block(self):
        index, value = 1, 31.12
        scratch_block = ["letter:of:", index, value]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)

        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.LETTER.toString() # @UndefinedVariable
        index_formula_element = catr_formula_element.leftChild
        value_formula_element = catr_formula_element.rightChild

        assert index_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert index_formula_element.value == str(index)
        assert index_formula_element.leftChild == None
        assert index_formula_element.rightChild == None

        assert value_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert value_formula_element.value == str(value)
        assert value_formula_element.leftChild == None
        assert value_formula_element.rightChild == None

    # letter:of:
    def test_can_convert_letter_of_string_block(self):
        index, value = 1, "dummyString"
        scratch_block = ["letter:of:", index, value]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)

        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.LETTER.toString() # @UndefinedVariable
        index_formula_element = catr_formula_element.leftChild
        value_formula_element = catr_formula_element.rightChild

        assert index_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert index_formula_element.value == str(index)
        assert index_formula_element.leftChild == None
        assert index_formula_element.rightChild == None

        assert value_formula_element.type == catformula.FormulaElement.ElementType.STRING
        assert value_formula_element.value == value
        assert value_formula_element.leftChild == None
        assert value_formula_element.rightChild == None

    # concatenate:with:
    def test_can_convert_concatenate_two_strings_block(self):
        value1 = "hello"
        value2 = "world"
        scratch_block = ["concatenate:with:", value1, value2]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)

        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.JOIN.toString() # @UndefinedVariable
        value1_formula_element = catr_formula_element.leftChild
        value2_formula_element = catr_formula_element.rightChild

        assert value1_formula_element.type == catformula.FormulaElement.ElementType.STRING
        assert value1_formula_element.value == value1
        assert value1_formula_element.leftChild == None
        assert value1_formula_element.rightChild == None

        assert value2_formula_element.type == catformula.FormulaElement.ElementType.STRING
        assert value2_formula_element.value == value2
        assert value2_formula_element.leftChild == None
        assert value2_formula_element.rightChild == None

    # concatenate:with:
    def test_can_convert_concatenate_two_numbers_block(self):
        value1, value2 = 1, 2
        scratch_block = ["concatenate:with:", value1, value2]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)

        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert catr_formula_element.value == catformula.Functions.JOIN.toString() # @UndefinedVariable
        value1_formula_element = catr_formula_element.leftChild
        value2_formula_element = catr_formula_element.rightChild

        assert value1_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert value1_formula_element.value == str(value1)
        assert value1_formula_element.leftChild == None
        assert value1_formula_element.rightChild == None

        assert value2_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert value2_formula_element.value == str(value2)
        assert value2_formula_element.leftChild == None
        assert value2_formula_element.rightChild == None

    # contains
    def test_can_convert_contains_brick(self):
        value1 = "Apple"
        value2 = "app"

        case_insensitivity_string = "(?ui)"
        empty_string = ""
        scratch_block = ["contains:", value1, value2]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)

        # inequality formula
        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.OPERATOR
        assert catr_formula_element.value == catformula.Operators.NOT_EQUAL.toString()
        assert catr_formula_element.leftChild is not None
        assert catr_formula_element.rightChild is not None

        # regex formula, left side of inequality
        regex_formula = catr_formula_element.leftChild
        assert regex_formula.type == catformula.FormulaElement.ElementType.FUNCTION
        assert regex_formula.value == catformula.Functions.REGEX.toString()
        assert regex_formula.leftChild is not None
        assert regex_formula.rightChild is not None

        # empty string, right side of inequality
        empty_string_formula = catr_formula_element.rightChild
        assert empty_string_formula.type == catformula.FormulaElement.ElementType.STRING
        assert empty_string_formula.value == empty_string

        # join formula, left child of regex
        join_formula = regex_formula.leftChild
        assert join_formula.type == catformula.FormulaElement.ElementType.FUNCTION
        assert join_formula.value == catformula.Functions.JOIN.toString()
        assert join_formula.leftChild is not None
        assert join_formula.rightChild is not None

        # extract the values from the formula
        value1_formula_element = regex_formula.rightChild
        value2_formula_element = join_formula.rightChild
        case_insensitivity_string_formula_element = join_formula.leftChild

        # check if '(?ui)' is in left child of the join formula
        assert case_insensitivity_string_formula_element.type == catformula.FormulaElement.ElementType.STRING
        assert case_insensitivity_string_formula_element.value == case_insensitivity_string
        assert case_insensitivity_string_formula_element.leftChild is None
        assert case_insensitivity_string_formula_element.rightChild is None

        # check if value1 was parsed correctly
        assert value1_formula_element.type == catformula.FormulaElement.ElementType.STRING
        assert value1_formula_element.value == value1
        assert value1_formula_element.leftChild is None
        assert value1_formula_element.rightChild is None

        # check if value2 was parsed correctly
        assert value2_formula_element.type == catformula.FormulaElement.ElementType.STRING
        assert value2_formula_element.value == value2
        assert value2_formula_element.leftChild is None
        assert value2_formula_element.rightChild is None

    #--------------------------------------------------------------------------------------------------------------
    # touching formula tests
    #--------------------------------------------------------------------------------------------------------------

    def test_can_convert_touching_block_mouse(self):
        scratch_block = ['touching:', '_mouse_']
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert str(catr_formula_element.getElementType()) == 'SENSOR'
        assert catr_formula_element.getValue() == 'COLLIDES_WITH_FINGER'

    def test_can_convert_touching_block_edge(self):
        scratch_block = ['touching:', '_edge_']
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert str(catr_formula_element.getElementType()) == 'SENSOR'
        assert catr_formula_element.getValue() == 'COLLIDES_WITH_EDGE'

    def test_can_convert_touching_block_object(self):
        scratch_block = ['touching:', '_some_object_']
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert str(catr_formula_element.getElementType()) == 'COLLISION_FORMULA'
        assert catr_formula_element.getValue() == '_some_object_'

    ###############################################################################################################
    #
    # Brick block tests
    #
    ###############################################################################################################

    def test_fail_on_unknown_block(self):
        #with self.assertRaises(common.ScratchtobatError):
        [catr_brick] = self.block_converter._catrobat_bricks_from(['wrong_block_name_zzz', 10, 10],
                                                                  DUMMY_CATR_SPRITE)
        # TODO: change to note-brick check later!!!
        #assert isinstance(catr_brick, catbricks.NoteBrick)
        assert isinstance(catr_brick, converter.UnmappedBlock)
        placeholder_brick = catr_brick.to_placeholder_brick()
        assert isinstance(placeholder_brick, list)
        assert len(placeholder_brick) == 1
        assert isinstance(placeholder_brick[0], catbricks.NoteBrick)

    # doIf
    def test_can_convert_if_block(self):
        expected_value_left_operand = "1"
        expected_value_right_operand = "2"
        scratch_do_if = ["doIf", ["=", expected_value_left_operand, expected_value_right_operand],
                         [["wait:elapsed:from:", 1], ["wait:elapsed:from:", 2]]]
        catr_do_if = self.block_converter._catrobat_bricks_from(scratch_do_if, DUMMY_CATR_SPRITE)

        assert isinstance(scratch_do_if, list)
        assert len(catr_do_if) == 1
        assert len(catr_do_if[0].ifBranchBricks) == 2

        brickList = catr_do_if + catr_do_if[0].ifBranchBricks
        expected_brick_classes = [catbricks.IfThenLogicBeginBrick, catbricks.WaitBrick, catbricks.WaitBrick]
        assert [_.__class__ for _ in brickList] == expected_brick_classes

        if_then_logic_begin_brick = catr_do_if[0]

        formula_tree_value = if_then_logic_begin_brick.getFormulaWithBrickField(catbasebrick.BrickField.IF_CONDITION).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.OPERATOR
        assert formula_tree_value.value == catformula.Operators.EQUAL.toString() # @UndefinedVariable
        assert formula_tree_value.leftChild is not None
        assert formula_tree_value.rightChild is not None

        formula_left_child = formula_tree_value.leftChild
        assert formula_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert expected_value_left_operand == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree_value.rightChild
        assert formula_right_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert expected_value_right_operand == formula_right_child.value
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

    # doIfElse
    def test_can_convert_if_else_block(self):
        expected_value_left_operand = "1"
        expected_value_right_operand = "2"
        scratch_do_if = ["doIfElse", ["=", expected_value_left_operand, expected_value_right_operand],
                         [["wait:elapsed:from:", 1]], [["wait:elapsed:from:", 2]]]
        catr_do_if = self.block_converter._catrobat_bricks_from(scratch_do_if, DUMMY_CATR_SPRITE)

        assert isinstance(scratch_do_if, list)
        assert len(catr_do_if) == 1
        assert len(catr_do_if[0].ifBranchBricks) == 1
        assert len(catr_do_if[0].elseBranchBricks) == 1
        expected_brick_classes = [catbricks.IfLogicBeginBrick, catbricks.WaitBrick,
                                  catbricks.WaitBrick,
                                  ]
        brickList = catr_do_if + catr_do_if[0].ifBranchBricks + catr_do_if[0].elseBranchBricks
        assert [_.__class__ for _ in brickList] == expected_brick_classes

        if_logic_begin_brick = catr_do_if[0]


        formula_tree_value = if_logic_begin_brick.getFormulaWithBrickField(catbasebrick.BrickField.IF_CONDITION).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.OPERATOR
        assert formula_tree_value.value == catformula.Operators.EQUAL.toString() # @UndefinedVariable
        assert formula_tree_value.leftChild is not None
        assert formula_tree_value.rightChild is not None

        formula_left_child = formula_tree_value.leftChild
        assert formula_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert expected_value_left_operand == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree_value.rightChild
        assert formula_right_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert expected_value_right_operand == formula_right_child.value
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

    # doRepeat
    def test_can_convert_loop_blocks(self):
        scratch_do_loop = ["doRepeat", 10, [[u'forward:', 10], [u'playDrum', 1, 0.2], [u'forward:', -10], [u'playDrum', 1, 0.2]]]
        catr_do_loop = self.block_converter._catrobat_bricks_from(scratch_do_loop, DUMMY_CATR_SPRITE)
        assert isinstance(catr_do_loop, list)
        # 1 loop start + 4 inner loop bricks +2 inner note bricks (playDrum not supported) + 1 loop end = 8
        assert len(catr_do_loop) == 1

        assert len(catr_do_loop[0].loopBricks) == 4
        expected_brick_classes = [catbricks.RepeatBrick, catbricks.MoveNStepsBrick, catbricks.NoteBrick,
                                  catbricks.MoveNStepsBrick, catbricks.NoteBrick]
        assert [_.__class__ for _ in catr_do_loop + catr_do_loop[0].loopBricks] == expected_brick_classes

    # doUntil
    def test_can_convert_do_until_block(self):
        expected_value_left_operand = "1"
        expected_value_right_operand = "2"
        scratch_block = ["doUntil", ["<", expected_value_left_operand, expected_value_right_operand],
                         [["forward:", 10], ["wait:elapsed:from:", 1]]]
        catr_do_until_loop = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_do_until_loop, list)
        assert len(catr_do_until_loop) == 1
        assert len(catr_do_until_loop[0].loopBricks) == 2
        brickList = catr_do_until_loop + catr_do_until_loop[0].loopBricks
        expected_brick_classes = [catbricks.RepeatUntilBrick, catbricks.MoveNStepsBrick,
                                  catbricks.WaitBrick]
        assert [_.__class__ for _ in brickList] == expected_brick_classes

        repeat_until_brick = catr_do_until_loop[0]
        assert isinstance(repeat_until_brick, catbricks.RepeatUntilBrick)
        formula_tree_value = repeat_until_brick.getFormulaWithBrickField(catbasebrick.BrickField.REPEAT_UNTIL_CONDITION).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.OPERATOR
        assert formula_tree_value.value == catformula.Operators.SMALLER_THAN.toString() # @UndefinedVariable
        assert formula_tree_value.leftChild is not None
        assert formula_tree_value.rightChild is not None

        formula_left_child = formula_tree_value.leftChild
        assert formula_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert expected_value_left_operand == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree_value.rightChild
        assert formula_right_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert expected_value_right_operand == formula_right_child.value
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

    # doWaitUntil
    def test_can_convert_do_wait_until_block(self):
        expected_value_left_operand = "1"
        expected_value_right_operand = "2"
        scratch_block = ["doWaitUntil", ["<", expected_value_left_operand, expected_value_right_operand]]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.WaitUntilBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.IF_CONDITION).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.OPERATOR
        assert formula_tree_value.value == catformula.Operators.SMALLER_THAN.toString() # @UndefinedVariable
        assert formula_tree_value.leftChild is not None
        assert formula_tree_value.rightChild is not None

        formula_left_child = formula_tree_value.leftChild
        assert formula_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert expected_value_left_operand == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree_value.rightChild
        assert formula_right_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert expected_value_right_operand == formula_right_child.value
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

    # stopScripts ("this script")
    def test_can_convert_stop_scripts_with_option_this_script_block(self):
        expected_index_of_option = 0
        scratch_block = ["stopScripts", "this script"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.StopScriptBrick)
        assert expected_index_of_option == catr_brick.spinnerSelection

    # stopScripts ("all")
    def test_can_convert_stop_scripts_with_option_all_scripts_block(self):
        expected_index_of_option = 1
        scratch_block = ["stopScripts", "all"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.StopScriptBrick)
        assert expected_index_of_option == catr_brick.spinnerSelection

    # stopScripts ("other scripts in sprite")
    def test_can_convert_stop_scripts_with_option_other_scripts_in_sprite_block(self):
        expected_index_of_option = 2
        scratch_block = ["stopScripts", "other scripts in sprite"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.StopScriptBrick)
        assert expected_index_of_option == catr_brick.spinnerSelection

    # stopScripts ("other scripts in stage")
    def test_can_convert_stop_scripts_with_option_other_scripts_in_stage_block(self):
        expected_index_of_option = 2
        scratch_block = ["stopScripts", "other scripts in stage"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.StopScriptBrick)
        assert expected_index_of_option == catr_brick.spinnerSelection

    # setRotationStyle ("left-right")
    def test_can_convert_set_rotation_style_with_option_left_right_block(self):
        expected_index_of_option = 0
        scratch_block = ["setRotationStyle", "left-right"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SetRotationStyleBrick)
        assert expected_index_of_option == catr_brick.selection

    # setRotationStyle ("all around")
    def test_can_convert_set_rotation_style_with_option_all_around_block(self):
        expected_index_of_option = 1
        scratch_block = ["setRotationStyle", "all around"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SetRotationStyleBrick)
        assert expected_index_of_option == catr_brick.selection

    # setRotationStyle ("don't rotate")
    def test_can_convert_set_rotation_style_with_option_dont_rotate_block(self):
        expected_index_of_option = 2
        scratch_block = ["setRotationStyle", "don't rotate"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SetRotationStyleBrick)
        assert expected_index_of_option == catr_brick.selection

    # broadcast:
    def test_can_convert_broadcast_block(self):
        broadcast_message = "hello world"
        scratch_block = ["broadcast:", broadcast_message]
        bricks = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert len(bricks) == 1
        broadcast_brick = bricks[0]
        assert isinstance(broadcast_brick, catbricks.BroadcastBrick)
        assert broadcast_brick.getBroadcastMessage() == broadcast_message

    # broadcast:
    def test_can_convert_broadcast_block_by_ignoring_case_sensitive_broadcast_message(self):
        broadcast_message = "hElLo WOrLD" # mixed case letters...
        scratch_block = ["broadcast:", broadcast_message]
        bricks = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert len(bricks) == 1
        broadcast_brick = bricks[0]
        assert isinstance(broadcast_brick, catbricks.BroadcastBrick)
        assert broadcast_brick.getBroadcastMessage() != broadcast_message
        assert broadcast_brick.getBroadcastMessage() == broadcast_message.lower()

    # doBroadcastAndWait
    def test_can_convert_doBroadcastAndWait_block(self):
        broadcast_message = "hello world"
        scratch_block = ["doBroadcastAndWait", broadcast_message]
        bricks = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert len(bricks) == 1
        broadcast_wait_brick = bricks[0]
        assert isinstance(broadcast_wait_brick, catbricks.BroadcastWaitBrick)
        assert broadcast_wait_brick.getBroadcastMessage() == broadcast_message

    # doBroadcastAndWait
    def test_can_convert_doBroadcastAndWait_block_by_ignoring_case_sensitive_broadcast_message(self):
        broadcast_message = "hElLo WOrLD" # mixed case letters...
        scratch_block = ["doBroadcastAndWait", broadcast_message]
        bricks = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert len(bricks) == 1
        broadcast_wait_brick = bricks[0]
        assert isinstance(broadcast_wait_brick, catbricks.BroadcastWaitBrick)
        assert broadcast_wait_brick.getBroadcastMessage() != broadcast_message
        assert broadcast_wait_brick.getBroadcastMessage() == broadcast_message.lower()

    # wait:elapsed:from:
    def test_can_convert_waitelapsedfrom_block(self):
        scratch_block = ["wait:elapsed:from:", 1]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.WaitBrick)
        formula_tree_seconds = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.TIME_TO_WAIT_IN_SECONDS).formulaTree # @UndefinedVariable
        assert formula_tree_seconds.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_tree_seconds.value == "1"

    # playSound:
    def test_can_convert_playsound_block_if_sound_missing(self):
        scratch_block = ["playSound:", "bird"]
        bricks = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert len(bricks) == 1
        assert isinstance(bricks[0], catbricks.PlaySoundBrick)
        assert bricks[0].sound is None

    # playSound:
    def test_can_convert_playsound_block(self):
        scratch_block = _, expected_sound_name = ["playSound:", "bird"]
        dummy_sprite = self.get_sprite_with_soundinfo(expected_sound_name)
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, dummy_sprite)
        assert isinstance(catr_brick, catbricks.PlaySoundBrick)
        assert catr_brick.sound.getName() == expected_sound_name

    # doPlaySoundAndWait
    def test_can_convert_playsoundandwait_block_if_sound_missing(self):
        scratch_block = ["doPlaySoundAndWait", "bird"]
        bricks = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert len(bricks) == 1
        assert isinstance(bricks[0], catbricks.PlaySoundAndWaitBrick)
        assert bricks[0].sound is None

    # doPlaySoundAndWait
    def test_can_convert_doplaysoundandwait_block(self):
        scratch_block = _, expected_sound_name = ["doPlaySoundAndWait", "bird"]
        dummy_sprite = self.get_sprite_with_soundinfo(expected_sound_name)
        [play_sound_and_wait_brick] = self.block_converter._catrobat_bricks_from(scratch_block, dummy_sprite)
        assert isinstance(play_sound_and_wait_brick, catbricks.PlaySoundAndWaitBrick)
        assert play_sound_and_wait_brick.sound.getName() == expected_sound_name

    # setGraphicEffect:to: (brightness)
    def test_can_convert_set_graphic_effect_with_float_value_brightness_block(self):
        scratch_block = _, _, expected_value = ["setGraphicEffect:to:", "brightness", 10.1]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SetBrightnessBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.BRIGHTNESS).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.OPERATOR
        assert formula_tree_value.value == catformula.Operators.PLUS.toString() # @UndefinedVariable
        assert formula_tree_value.leftChild is not None
        assert formula_tree_value.rightChild is not None

        formula_left_child = formula_tree_value.leftChild
        assert formula_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_value) == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree_value.rightChild
        assert formula_right_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert "100" == formula_right_child.value # offset 100 due to range-conversion!
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

    # setGraphicEffect:to: (brightness)
    def test_can_convert_set_graphic_effect_with_formula_value_brightness_block(self):
        expected_left_operand = 10.1
        expected_right_operand = 1
        scratch_block = ["setGraphicEffect:to:", "brightness", ["+", expected_left_operand,
                                                                expected_right_operand]]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SetBrightnessBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.BRIGHTNESS).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.OPERATOR
        assert formula_tree_value.value == catformula.Operators.PLUS.toString() # @UndefinedVariable
        assert formula_tree_value.leftChild is not None
        assert formula_tree_value.rightChild is not None

        formula_left_child = formula_tree_value.leftChild
        assert formula_left_child.type == catformula.FormulaElement.ElementType.OPERATOR
        assert formula_left_child.value == catformula.Operators.PLUS.toString() # @UndefinedVariable
        assert formula_left_child.leftChild is not None
        assert formula_left_child.rightChild is not None

        formula_left_child_left_child = formula_left_child.leftChild
        assert formula_left_child_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_left_operand) == formula_left_child_left_child.value
        assert formula_left_child_left_child.leftChild is None
        assert formula_left_child_left_child.rightChild is None

        formula_right_child_right_child = formula_left_child.rightChild
        assert formula_right_child_right_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_right_operand) == formula_right_child_right_child.value
        assert formula_right_child_right_child.leftChild is None
        assert formula_right_child_right_child.rightChild is None

        formula_right_child = formula_tree_value.rightChild
        assert formula_right_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert "100" == formula_right_child.value # offset 100 due to range-conversion!
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

    # setGraphicEffect:to: (ghost)
    def test_can_convert_set_graphic_effect_with_float_value_ghost_block(self):
        scratch_block = _, _, expected_value = ["setGraphicEffect:to:", "ghost", 10.2]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SetTransparencyBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.TRANSPARENCY).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_value) == formula_tree_value.value
        assert formula_tree_value.leftChild is None
        assert formula_tree_value.rightChild is None

    # setGraphicEffect:to: (ghost)
    def test_can_convert_set_graphic_effect_with_formula_value_ghost_block(self):
        expected_left_operand = 10.2
        expected_right_operand = 1
        scratch_block = ["setGraphicEffect:to:", "ghost", ["+", expected_left_operand, expected_right_operand]]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SetTransparencyBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.TRANSPARENCY).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.OPERATOR
        assert formula_tree_value.value == catformula.Operators.PLUS.toString() # @UndefinedVariable
        assert formula_tree_value.leftChild is not None
        assert formula_tree_value.rightChild is not None

        formula_left_child = formula_tree_value.leftChild
        assert formula_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_left_operand) == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree_value.rightChild
        assert formula_right_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_right_operand) == formula_right_child.value
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

    # setGraphicEffect:to: (color)
    def test_can_convert_set_graphic_effect_with_float_value_color_block(self):
        scratch_block = _, _, expected_value = ["setGraphicEffect:to:", "color", 10.2]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SetColorBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.COLOR).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_value) == formula_tree_value.value
        assert formula_tree_value.leftChild is None
        assert formula_tree_value.rightChild is None

    # setGraphicEffect:to: (color)
    def test_can_convert_set_graphic_effect_with_formula_value_color_block(self):
        expected_left_operand = 10.2
        expected_right_operand = 1
        scratch_block = ["setGraphicEffect:to:", "color", ["+", expected_left_operand, expected_right_operand]]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SetColorBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.COLOR).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.OPERATOR
        assert formula_tree_value.value == catformula.Operators.PLUS.toString() # @UndefinedVariable
        assert formula_tree_value.leftChild is not None
        assert formula_tree_value.rightChild is not None

        formula_left_child = formula_tree_value.leftChild
        assert formula_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_left_operand) == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree_value.rightChild
        assert formula_right_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_right_operand) == formula_right_child.value
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

    # changeGraphicEffect:by: (brightness)
    def test_can_convert_change_graphic_effect_with_float_value_brightness_block(self):
        scratch_block = _, _, expected_value = ["changeGraphicEffect:by:", "brightness", 10.1]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ChangeBrightnessByNBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.BRIGHTNESS_CHANGE).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_value) == formula_tree_value.value
        assert formula_tree_value.leftChild is None
        assert formula_tree_value.rightChild is None

    # changeGraphicEffect:by: (brightness)
    def test_can_convert_change_graphic_effect_with_formula_value_brightness_block(self):
        expected_left_operand = 10.2
        expected_right_operand = 1
        scratch_block = ["changeGraphicEffect:by:", "brightness", ["+", expected_left_operand, expected_right_operand]]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ChangeBrightnessByNBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.BRIGHTNESS_CHANGE).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.OPERATOR
        assert formula_tree_value.value == catformula.Operators.PLUS.toString() # @UndefinedVariable
        assert formula_tree_value.leftChild is not None
        assert formula_tree_value.rightChild is not None

        formula_left_child = formula_tree_value.leftChild
        assert formula_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_left_operand) == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree_value.rightChild
        assert formula_right_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_right_operand) == formula_right_child.value
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

    # changeGraphicEffect:by: (ghost)
    def test_can_convert_change_graphic_effect_with_float_value_ghost_block(self):
        scratch_block = _, _, expected_value = ["changeGraphicEffect:by:", "ghost", 10.2]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ChangeTransparencyByNBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.TRANSPARENCY_CHANGE).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_value) == formula_tree_value.value
        assert formula_tree_value.leftChild is None
        assert formula_tree_value.rightChild is None

    # changeGraphicEffect:by: (ghost)
    def test_can_convert_change_graphic_effect_with_formula_value_ghost_block(self):
        expected_left_operand = 10.2
        expected_right_operand = 1
        scratch_block = ["changeGraphicEffect:by:", "ghost", ["+", expected_left_operand, expected_right_operand]]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ChangeTransparencyByNBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.TRANSPARENCY_CHANGE).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.OPERATOR
        assert formula_tree_value.value == catformula.Operators.PLUS.toString() # @UndefinedVariable
        assert formula_tree_value.leftChild is not None
        assert formula_tree_value.rightChild is not None

        formula_left_child = formula_tree_value.leftChild
        assert formula_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_left_operand) == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree_value.rightChild
        assert formula_right_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_right_operand) == formula_right_child.value
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

    # changeGraphicEffect:by: (color)
    def test_can_convert_change_graphic_effect_with_float_value_color_block(self):
        scratch_block = _, _, expected_value = ["changeGraphicEffect:by:", "color", 10.2]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ChangeColorByNBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.COLOR_CHANGE).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_value) == formula_tree_value.value
        assert formula_tree_value.leftChild is None
        assert formula_tree_value.rightChild is None

    # changeGraphicEffect:by: (color)
    def test_can_convert_change_graphic_effect_with_formula_value_color_block(self):
        expected_left_operand = 10.2
        expected_right_operand = 1
        scratch_block = ["changeGraphicEffect:by:", "color", ["+", expected_left_operand, expected_right_operand]]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ChangeColorByNBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.COLOR_CHANGE).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.OPERATOR
        assert formula_tree_value.value == catformula.Operators.PLUS.toString() # @UndefinedVariable
        assert formula_tree_value.leftChild is not None
        assert formula_tree_value.rightChild is not None

        formula_left_child = formula_tree_value.leftChild
        assert formula_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_left_operand) == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree_value.rightChild
        assert formula_right_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_right_operand) == formula_right_child.value
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

    # append:toList:
    def test_can_convert_append_number_to_list_block(self):
        value = "1.23"
        scratch_block = ["append:toList:", value, self._name_of_test_list]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.AddItemToUserListBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.LIST_ADD_ITEM).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_tree_value.value == value
        assert formula_tree_value.leftChild == None
        assert formula_tree_value.rightChild == None

    # append:toList:
    def test_can_convert_append_str_to_list_block(self):
        value = "DummyString"
        scratch_block = ["append:toList:", value, self._name_of_test_list]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.AddItemToUserListBrick)
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.LIST_ADD_ITEM).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.STRING
        assert formula_tree_value.value == value
        assert formula_tree_value.leftChild == None
        assert formula_tree_value.rightChild == None

    # insert:at:ofList:
    def test_can_convert_insert_numeric_value_at_numeric_index_in_list_block(self):
        index, value = 2, "1.23"
        scratch_block = ["insert:at:ofList:", value, index, self._name_of_test_list]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.InsertItemIntoUserListBrick)

        formula_tree_index = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.INSERT_ITEM_INTO_USERLIST_INDEX).formulaTree # @UndefinedVariable
        assert formula_tree_index.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_tree_index.value == str(index)
        assert formula_tree_index.leftChild == None
        assert formula_tree_index.rightChild == None
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.INSERT_ITEM_INTO_USERLIST_VALUE).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_tree_value.value == value
        assert formula_tree_value.leftChild == None
        assert formula_tree_value.rightChild == None

    # insert:at:ofList:
    def test_can_convert_insert_string_at_last_position_in_list_block(self):
        value = "DummyString"
        scratch_block = ["insert:at:ofList:", value, "last", self._name_of_test_list]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.AddItemToUserListBrick)

        formula_tree_index = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.LIST_ADD_ITEM).formulaTree # @UndefinedVariable
        assert formula_tree_index.type == catformula.FormulaElement.ElementType.STRING
        assert formula_tree_index.value == "DummyString"

    # insert:at:ofList:
    def test_can_convert_insert_at_random_position_in_list_block(self):
        value = "DummyString"
        scratch_block = ["insert:at:ofList:", value, "random", self._name_of_test_list]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.InsertItemIntoUserListBrick)

        formula_tree_index = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.INSERT_ITEM_INTO_USERLIST_INDEX).formulaTree # @UndefinedVariable
        assert formula_tree_index.type == catformula.FormulaElement.ElementType.FUNCTION
        assert formula_tree_index.value == "RAND"
        assert formula_tree_index.leftChild
        assert formula_tree_index.rightChild
        formula_element_left_child = formula_tree_index.leftChild
        assert formula_element_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_element_left_child.value == "1"
        assert formula_element_left_child.leftChild == None
        assert formula_element_left_child.rightChild == None
        formula_element_right_child = formula_tree_index.rightChild
        assert formula_element_right_child.type == catformula.FormulaElement.ElementType.FUNCTION
        assert formula_element_right_child.value == "NUMBER_OF_ITEMS"
        assert formula_element_right_child.leftChild
        assert formula_element_right_child.rightChild == None
        formula_element_inner_left_child = formula_element_right_child.leftChild
        assert formula_element_inner_left_child.type == catformula.FormulaElement.ElementType.USER_LIST
        assert formula_element_inner_left_child.value == self._name_of_test_list
        assert formula_element_inner_left_child.leftChild == None
        assert formula_element_inner_left_child.rightChild == None
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.INSERT_ITEM_INTO_USERLIST_VALUE).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.STRING
        assert formula_tree_value.value == value
        assert formula_tree_value.leftChild == None
        assert formula_tree_value.rightChild == None

    # deleteLine:ofList:
    def test_can_convert_delete_line_from_list_by_index_block(self):
        index = 2
        scratch_block = ["deleteLine:ofList:", index, self._name_of_test_list]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.DeleteItemOfUserListBrick)
        formula_tree_list_delete_item = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.LIST_DELETE_ITEM).formulaTree # @UndefinedVariable
        assert formula_tree_list_delete_item.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_tree_list_delete_item.value == str(index)

    # deleteLine:ofList:
    def test_can_convert_delete_last_line_from_list_block(self):
        scratch_block = ["deleteLine:ofList:", "last", self._name_of_test_list]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.DeleteItemOfUserListBrick)

        formula_tree_list_delete_item = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.LIST_DELETE_ITEM).formulaTree # @UndefinedVariable
        assert formula_tree_list_delete_item.type == catformula.FormulaElement.ElementType.FUNCTION
        assert formula_tree_list_delete_item.value == "NUMBER_OF_ITEMS"
        assert formula_tree_list_delete_item.leftChild
        assert formula_tree_list_delete_item.rightChild == None
        formula_element_left_child = formula_tree_list_delete_item.leftChild
        assert formula_element_left_child.type == catformula.FormulaElement.ElementType.USER_LIST
        assert formula_element_left_child.value == self._name_of_test_list
        assert formula_element_left_child.leftChild == None
        assert formula_element_left_child.rightChild == None

    # deleteLine:ofList:
    def test_can_convert_delete_all_lines_from_list_block(self):
        scratch_block = ["deleteLine:ofList:", "all", self._name_of_test_list]
        catr_brick_list = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)

        assert len(catr_brick_list) == 1
        assert isinstance(catr_brick_list[0], catbricks.RepeatBrick)
        assert len(catr_brick_list[0].loopBricks) == 1
        assert isinstance(catr_brick_list[0].loopBricks[0], catbricks.DeleteItemOfUserListBrick)

        formula_tree_times_to_repeat = catr_brick_list[0].getFormulaWithBrickField(catbasebrick.BrickField.TIMES_TO_REPEAT).formulaTree # @UndefinedVariable
        assert formula_tree_times_to_repeat.type == catformula.FormulaElement.ElementType.FUNCTION
        assert formula_tree_times_to_repeat.value == "NUMBER_OF_ITEMS"
        assert formula_tree_times_to_repeat.leftChild
        assert formula_tree_times_to_repeat.rightChild == None
        formula_element_left_child = formula_tree_times_to_repeat.leftChild
        assert formula_element_left_child.type == catformula.FormulaElement.ElementType.USER_LIST
        assert formula_element_left_child.value == self._name_of_test_list
        assert formula_element_left_child.leftChild == None
        assert formula_element_left_child.rightChild == None

        formula_tree_list_delete_item = catr_brick_list[0].loopBricks[0].getFormulaWithBrickField(catbasebrick.BrickField.LIST_DELETE_ITEM).formulaTree # @UndefinedVariable
        assert formula_tree_list_delete_item.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_tree_list_delete_item.value == "1"
        assert formula_tree_list_delete_item.leftChild == None
        assert formula_tree_list_delete_item.rightChild == None


    # setLine:ofList:to:
    def test_can_convert_set_line_via_str_index_of_list_to_block(self):
        index, value = "2", "1"
        scratch_block = ["setLine:ofList:to:", index, self._name_of_test_list, value]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ReplaceItemInUserListBrick)

        formula_tree_index = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.REPLACE_ITEM_IN_USERLIST_INDEX).formulaTree # @UndefinedVariable
        assert formula_tree_index.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_tree_index.value == index
        assert formula_tree_index.leftChild == None
        assert formula_tree_index.rightChild == None

        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.REPLACE_ITEM_IN_USERLIST_VALUE).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_tree_value.value == value
        assert formula_tree_value.leftChild == None
        assert formula_tree_value.rightChild == None

    # setLine:ofList:to:
    def test_can_convert_set_line_via_numeric_index_of_list_to_block(self):
        index, value = 2, "1"
        scratch_block = ["setLine:ofList:to:", index, self._name_of_test_list, value]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ReplaceItemInUserListBrick)

        formula_tree_index = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.REPLACE_ITEM_IN_USERLIST_INDEX).formulaTree # @UndefinedVariable
        assert formula_tree_index.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_tree_index.value == str(index)
        assert formula_tree_index.leftChild == None
        assert formula_tree_index.rightChild == None

        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.REPLACE_ITEM_IN_USERLIST_VALUE).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_tree_value.value == value
        assert formula_tree_value.leftChild == None
        assert formula_tree_value.rightChild == None

    # setLine:ofList:to:
    def test_can_convert_set_last_line_of_list_to_block(self):
        value = "1"
        scratch_block = ["setLine:ofList:to:", "last", self._name_of_test_list, value]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ReplaceItemInUserListBrick)

        formula_tree_index = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.REPLACE_ITEM_IN_USERLIST_INDEX).formulaTree # @UndefinedVariable
        assert formula_tree_index.type == catformula.FormulaElement.ElementType.FUNCTION
        assert formula_tree_index.value == catformula.Functions.NUMBER_OF_ITEMS.toString() # @UndefinedVariable
        assert formula_tree_index.leftChild
        assert formula_tree_index.rightChild == None
        formula_element_left_child = formula_tree_index.leftChild
        assert formula_element_left_child.type == catformula.FormulaElement.ElementType.USER_LIST
        assert formula_element_left_child.value == self._name_of_test_list
        assert formula_element_left_child.leftChild == None
        assert formula_element_left_child.rightChild == None

        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.REPLACE_ITEM_IN_USERLIST_VALUE).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_tree_value.value == value
        assert formula_tree_value.leftChild == None
        assert formula_tree_value.rightChild == None

    # setLine:ofList:to:
    def test_can_convert_set_random_line_of_list_to_with_numeric_value_block(self):
        value = "1.23"
        scratch_block = ["setLine:ofList:to:", "random", self._name_of_test_list, value]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ReplaceItemInUserListBrick)

        formula_tree_index = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.REPLACE_ITEM_IN_USERLIST_INDEX).formulaTree # @UndefinedVariable
        assert formula_tree_index.type == catformula.FormulaElement.ElementType.FUNCTION
        assert formula_tree_index.value == "RAND"
        assert formula_tree_index.leftChild
        assert formula_tree_index.rightChild
        formula_element_left_child = formula_tree_index.leftChild
        assert formula_element_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_element_left_child.value == "1"
        assert formula_element_left_child.leftChild == None
        assert formula_element_left_child.rightChild == None
        formula_element_right_child = formula_tree_index.rightChild
        assert formula_element_right_child.type == catformula.FormulaElement.ElementType.FUNCTION
        assert formula_element_right_child.value == "NUMBER_OF_ITEMS"
        assert formula_element_right_child.leftChild
        assert formula_element_right_child.rightChild == None
        formula_element_inner_left_child = formula_element_right_child.leftChild
        assert formula_element_inner_left_child.type == catformula.FormulaElement.ElementType.USER_LIST
        assert formula_element_inner_left_child.value == self._name_of_test_list
        assert formula_element_inner_left_child.leftChild == None
        assert formula_element_inner_left_child.rightChild == None
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.REPLACE_ITEM_IN_USERLIST_VALUE).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_tree_value.value == value
        assert formula_tree_value.leftChild == None
        assert formula_tree_value.rightChild == None

    # nextCostume
    def test_can_convert_nextcostume_block(self):
        scratch_block = ["nextCostume"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.NextLookBrick)

    # setVideoState
    def test_can_convert_setvideostate_block_with_state_on(self):
        scratch_block = ["setVideoState", "on"]
        [choose_camera_brick, camera_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(choose_camera_brick, catbricks.ChooseCameraBrick)
        assert isinstance(camera_brick, catbricks.CameraBrick)
        assert choose_camera_brick.spinnerSelectionID == catbricks.ChooseCameraBrick.FRONT # @UndefinedVariable
        assert camera_brick.spinnerSelectionID == catbricks.CameraBrick.ON                 # @UndefinedVariable

    # setVideoState
    def test_can_convert_setvideostate_block_with_state_off(self):
        scratch_block = ["setVideoState", "off"]
        [choose_camera_brick, camera_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(choose_camera_brick, catbricks.ChooseCameraBrick)
        assert isinstance(camera_brick, catbricks.CameraBrick)
        assert choose_camera_brick.spinnerSelectionID == catbricks.ChooseCameraBrick.FRONT # @UndefinedVariable
        assert camera_brick.spinnerSelectionID == catbricks.CameraBrick.OFF                # @UndefinedVariable

    # setVideoState
    def test_can_convert_setvideostate_block_with_state_on_flipped(self):
        scratch_block = ["setVideoState", "on-flipped"]
        [choose_camera_brick, camera_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(choose_camera_brick, catbricks.ChooseCameraBrick)
        assert isinstance(camera_brick, catbricks.CameraBrick)
        assert choose_camera_brick.spinnerSelectionID == catbricks.ChooseCameraBrick.FRONT # @UndefinedVariable
        assert camera_brick.spinnerSelectionID == catbricks.CameraBrick.ON                 # @UndefinedVariable

    # glideSecs:toX:y:elapsed:from:
    def test_can_convert_glideto_block(self):
        scratch_block = _, glide_duration, glide_x, glide_y = ["glideSecs:toX:y:elapsed:from:", 5, 174, -122]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.GlideToBrick)
        durationInSecondsFormula = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.DURATION_IN_SECONDS) # @UndefinedVariable
        xDestinationFormula = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.X_DESTINATION) # @UndefinedVariable
        yDestinationFormula = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.Y_DESTINATION) # @UndefinedVariable
        assert int(float(durationInSecondsFormula.formulaTree.getValue())) == glide_duration
        assert int(float(xDestinationFormula.formulaTree.getValue())) == glide_x
        assert -1 * int(float(yDestinationFormula.formulaTree.rightChild.getValue())) == glide_y

    # mousePressed
    def test_can_convert_mouse_pressed_block(self):
        scratch_block = ["mousePressed"]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.SENSOR
        assert catr_formula_element.value == catformula.Sensors.FINGER_TOUCHED.toString() # @UndefinedVariable
        assert catr_formula_element.leftChild == None
        assert catr_formula_element.rightChild == None

    # mouseX
    def test_can_convert_mouse_x_block(self):
        scratch_block = ["mouseX"]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.SENSOR
        assert catr_formula_element.value == catformula.Sensors.FINGER_X.toString() # @UndefinedVariable
        assert catr_formula_element.leftChild == None
        assert catr_formula_element.rightChild == None

    # mouseY
    def test_can_convert_mouse_y_block(self):
        scratch_block = ["mouseY"]
        [catr_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_formula_element, catformula.FormulaElement)
        assert catr_formula_element.type == catformula.FormulaElement.ElementType.SENSOR
        assert catr_formula_element.value == catformula.Sensors.FINGER_Y.toString() # @UndefinedVariable
        assert catr_formula_element.leftChild == None
        assert catr_formula_element.rightChild == None

    # startScene
    def test_can_convert_startscene_block(self):
        scratch_script= scratch.Script([321, 89, [["whenSceneStarts", "look1"], ["startScene", "look2"]]])
        self.test_project.getDefaultScene().spriteList.add(self.sprite_stub)
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE, self.test_project)
        assert isinstance(catr_script.getBrickList()[0], catbricks.SetBackgroundBrick)
        assert catr_script.getBrickList()[0].getLook().getName() == "look2"
        assert catr_script.getBrickList()[0].getLook() == self.sprite_stub.getLookList()[1]
        assert len(catr_script.getBrickList()) == 1

    # startScene
    def test_can_convert_startscene_next_backdrop_block(self):
        scratch_block = ["startScene", "next backdrop"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, create_catrobat_background_sprite_stub())
        assert isinstance(catr_brick, catbricks.NextLookBrick)

    # startScene
    def test_can_convert_startscene_previous_backdrop_block(self):
        scratch_block = ["startScene", "previous backdrop"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, create_catrobat_background_sprite_stub())
        assert isinstance(catr_brick, catbricks.PreviousLookBrick)

    # startSceneAndWait
    def test_can_convert_startscene_wait_block(self):
        scratch_script= scratch.Script([321, 89, [["whenSceneStarts", "look1"], ["startSceneAndWait", "look2"]]])
        self.test_project.getDefaultScene().spriteList.add(self.sprite_stub)
        background_stub = create_catrobat_background_sprite_stub()
        catr_script = self.block_converter._catrobat_script_from(scratch_script, background_stub, self.test_project)
        assert isinstance(catr_script.getBrickList()[0], catbricks.SetBackgroundAndWaitBrick)
        assert catr_script.getBrickList()[0].getLook().getName() == "look2"
        assert catr_script.getBrickList()[0].getLook() == background_stub.getLookList()[1]
        assert len(catr_script.getBrickList()) == 1

    # startSceneAndWait
    def test_can_convert_startscene_wait_next_backdrop_block(self):
        scratch_block = ["startSceneAndWait", "next backdrop"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, create_catrobat_background_sprite_stub())
        assert isinstance(catr_brick, catbricks.NextLookBrick)

    # startSceneAndWait
    def test_can_convert_startscene_wait_previous_backdrop_block(self):
        scratch_block = ["startSceneAndWait", "previous backdrop"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, create_catrobat_background_sprite_stub())
        assert isinstance(catr_brick, catbricks.PreviousLookBrick)

    # sayBubbleBrick
    def test_can_convert_say_bubble_brick(self):
        scratch_block = _, expected_message = ["say:", "Hello!"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SayBubbleBrick)
        formula_tree_message = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.STRING).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.STRING == formula_tree_message.type
        assert expected_message == formula_tree_message.value
        assert formula_tree_message.leftChild is None
        assert formula_tree_message.rightChild is None

    # sayForBubbleBrick
    def test_can_convert_say_for_bubble_brick(self):
        scratch_block = _, expected_message, expected_duration = ["say:duration:elapsed:from:", "Hello!", 2]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SayForBubbleBrick)

        formula_tree_message = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.STRING).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.STRING == formula_tree_message.type
        assert expected_message == formula_tree_message.value
        assert formula_tree_message.leftChild is None
        assert formula_tree_message.rightChild is None

        formula_tree_duration = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.DURATION_IN_SECONDS).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.NUMBER == formula_tree_duration.type
        assert str(float(expected_duration)) == formula_tree_duration.value
        assert formula_tree_duration.leftChild is None
        assert formula_tree_duration.rightChild is None

    # sayBubbleBrick
    def test_can_convert_say_bubble_brick_with_formulas(self):
        expected_left_operand = 1
        expected_right_operand = 2
        scratch_block = ["say:", ["+", expected_left_operand, expected_right_operand]]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SayBubbleBrick)

        formula_tree = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.STRING).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.OPERATOR == formula_tree.type
        assert formula_tree.value == catformula.Operators.PLUS.toString() # @UndefinedVariable
        assert formula_tree.leftChild is not None
        assert formula_tree.rightChild is not None

        formula_left_child = formula_tree.leftChild
        assert catformula.FormulaElement.ElementType.NUMBER == formula_left_child.type
        assert str(expected_left_operand) == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree.rightChild
        assert catformula.FormulaElement.ElementType.NUMBER == formula_right_child.type
        assert str(expected_right_operand) == formula_right_child.value
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

    # sayForBubbleBrick
    def test_can_convert_say_for_bubble_brick_with_formulas(self):
        expected_left_operand = 1
        expected_right_operand = 2
        scratch_block = _, expected_message, _ = ["say:duration:elapsed:from:", "Hello!",
                                                  ["+", expected_left_operand, expected_right_operand]]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SayForBubbleBrick)

        formula_tree = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.STRING).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.STRING == formula_tree.type
        assert expected_message == formula_tree.value
        assert formula_tree.leftChild is None
        assert formula_tree.rightChild is None

        formula_tree = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.DURATION_IN_SECONDS).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.OPERATOR == formula_tree.type
        assert formula_tree.value == catformula.Operators.PLUS.toString() # @UndefinedVariable
        assert formula_tree.leftChild is not None
        assert formula_tree.rightChild is not None

        formula_left_child = formula_tree.leftChild
        assert catformula.FormulaElement.ElementType.NUMBER == formula_left_child.type
        assert str(expected_left_operand) == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree.rightChild
        assert catformula.FormulaElement.ElementType.NUMBER == formula_right_child.type
        assert str(expected_right_operand) == formula_right_child.value
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

    # think:
    def test_can_convert_think_bubble_brick(self):
        scratch_block = _, expected_message = ["think:", "2B or !2B..."]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ThinkBubbleBrick)

        formula_tree = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.STRING).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.STRING == formula_tree.type
        assert expected_message == formula_tree.value
        assert formula_tree.leftChild is None
        assert formula_tree.rightChild is None

    # think:duration:elapsed:from:
    def test_can_convert_think_for_bubble_brick(self):
        scratch_block = _, expected_message, expected_duration = ["think:duration:elapsed:from:", "2B or !2B...", 2]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ThinkForBubbleBrick)

        formula_tree = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.STRING).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.STRING == formula_tree.type
        assert expected_message == formula_tree.value
        assert formula_tree.leftChild is None
        assert formula_tree.rightChild is None

        formula_tree_duration = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.DURATION_IN_SECONDS).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.NUMBER == formula_tree_duration.type
        assert str(expected_duration) == formula_tree_duration.value
        assert formula_tree_duration.leftChild is None
        assert formula_tree_duration.rightChild is None

    # doAsk (with question as string)
    def test_can_convert_do_ask_with_question_as_string_block(self):
        sprite_context = converter.SpriteContext(DUMMY_CATR_SPRITE.getName(), {})
        script_context = converter.ScriptContext(sprite_context)
        scratch_block = _, expected_question_string = ["doAsk", "What's your name?"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE, script_context)
        assert isinstance(catr_brick, catbricks.AskBrick)

        formula_tree = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.ASK_QUESTION).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.STRING == formula_tree.type
        assert expected_question_string == formula_tree.value
        assert formula_tree.leftChild is None
        assert formula_tree.rightChild is None

        user_variable = catr_brick.getUserVariable()
        assert user_variable is not None
        assert isinstance(user_variable, catformula.UserVariable)
        assert converter._SHARED_GLOBAL_ANSWER_VARIABLE_NAME == user_variable.getName()

        project = self.block_converter._catrobat_project
        assert user_variable == project.getUserVariable(converter._SHARED_GLOBAL_ANSWER_VARIABLE_NAME)

    # doAsk (with question as formula)
    def test_can_convert_do_ask_with_question_as_formula_block(self):
        expected_left_operand = 1
        expected_right_operand = 2
        sprite_context = converter.SpriteContext(DUMMY_CATR_SPRITE.getName(), {})
        script_context = converter.ScriptContext(sprite_context)
        scratch_block = ["doAsk", ["+", expected_left_operand, expected_right_operand]]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE,
                                                                  script_context)
        assert isinstance(catr_brick, catbricks.AskBrick)

        formula_tree = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.ASK_QUESTION).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.OPERATOR == formula_tree.type
        assert formula_tree.value == catformula.Operators.PLUS.toString() # @UndefinedVariable
        assert formula_tree.leftChild is not None
        assert formula_tree.rightChild is not None

        formula_left_child = formula_tree.leftChild
        assert catformula.FormulaElement.ElementType.NUMBER == formula_left_child.type
        assert str(expected_left_operand) == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree.rightChild
        assert catformula.FormulaElement.ElementType.NUMBER == formula_right_child.type
        assert str(expected_right_operand) == formula_right_child.value
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

        user_variable = catr_brick.getUserVariable()
        assert user_variable is not None
        assert isinstance(user_variable, catformula.UserVariable)
        assert converter._SHARED_GLOBAL_ANSWER_VARIABLE_NAME == user_variable.getName()

        project = self.block_converter._catrobat_project
        assert user_variable == project.getUserVariable(converter._SHARED_GLOBAL_ANSWER_VARIABLE_NAME)

    # answer
    def test_can_convert_answer_block(self):
        sprite_context = converter.SpriteContext(DUMMY_CATR_SPRITE.getName(), {})
        script_context = converter.ScriptContext(sprite_context)
        [formula_element] = self.block_converter._catrobat_bricks_from(["answer"], DUMMY_CATR_SPRITE,
                                                                       script_context)
        assert isinstance(formula_element, catformula.FormulaElement)
        assert catformula.FormulaElement.ElementType.USER_VARIABLE == formula_element.type
        assert converter._SHARED_GLOBAL_ANSWER_VARIABLE_NAME == formula_element.value
        assert formula_element.leftChild is None
        assert formula_element.rightChild is None

        project = self.block_converter._catrobat_project
        user_variable = project.getUserVariable(converter._SHARED_GLOBAL_ANSWER_VARIABLE_NAME)
        assert user_variable is not None
        assert converter._SHARED_GLOBAL_ANSWER_VARIABLE_NAME == user_variable.getName()

    # createCloneOf
    def test_can_convert_create_clone_of_block_myself(self):
        sprite_name = '_myself_'
        scratch_block = ["createCloneOf", sprite_name]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.CloneBrick)
        assert DUMMY_CATR_SPRITE.getName() == catr_brick.objectToClone.getName()
        assert DUMMY_CATR_SPRITE is catr_brick.objectToClone

    # createCloneOf
    def test_fail_convert_create_clone_of_block_with_empty_string_arg(self):
        sprite_name = ""
        scratch_block = ["createCloneOf", sprite_name]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.NoteBrick)

    # createCloneOf
    def test_fail_convert_create_clone_of_block_with_formula_arg(self):
        scratch_block = ["createCloneOf", ["-", 2, 1]]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.NoteBrick)

    # createCloneOf
    def test_convert_create_clone_of_block_previous(self):
        sprite_object = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, "Previous")
        self.test_scene.spriteList.append(sprite_object)

        scratch_block = ["createCloneOf", "Previous"]

        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.CloneBrick)
        assert catr_brick.objectToClone.getName() == "Previous"
        assert sprite_object is catr_brick.objectToClone

    # createCloneOf
    def test_convert_create_clone_of_block_afterwards(self):
        #context = self.block_converter._context
        context = converter.Context()
        sprite_context = converter.SpriteContext(DUMMY_CATR_SPRITE.getName(), {})
        sprite_context.context = context
        script_context = converter.ScriptContext(sprite_context)
        scratch_block = ["createCloneOf", "Afterwards"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE, script_context)
        assert isinstance(catr_brick, catbricks.CloneBrick)
        assert catr_brick.objectToClone.getName() == "Afterwards"
        assert "Afterwards" in context.upcoming_sprites
        assert catr_brick.objectToClone is context.upcoming_sprites["Afterwards"]

    # whenCloned
    def test_can_convert_when_cloned_block(self):
        scratch_block = ["say:", "Hello!"]
        script = scratch.Script([30, 355, [['whenCloned'], scratch_block]])
        catr_script = self.block_converter._catrobat_script_from(script, self.sprite_stub, self.test_project)
        assert isinstance(catr_script, catbase.WhenClonedScript)
        assert isinstance(catr_script.getBrickList().get(0), catbricks.SayBubbleBrick)

    # deleteClone
    def test_can_convert_delete_clone_block(self):
        scratch_block = ["deleteClone"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.DeleteThisCloneBrick)

    # timeAndDate
    def test_can_convert_time_and_date_block_second(self):
        scratch_block = ["timeAndDate", "second"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catformula.FormulaElement)
        assert catr_brick.getValue() == str(catformula.Sensors.TIME_SECOND)

    # timeAndDate
    def test_can_convert_time_and_date_block_minute(self):
        scratch_block = ["timeAndDate", "minute"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catformula.FormulaElement)
        assert catr_brick.getValue() == str(catformula.Sensors.TIME_MINUTE)

    # timeAndDate
    def test_can_convert_time_and_date_block_hour(self):
        scratch_block = ["timeAndDate", "hour"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catformula.FormulaElement)
        assert catr_brick.getValue() == str(catformula.Sensors.TIME_HOUR)

    # timeAndDate
    def test_can_convert_time_and_date_block_weekday(self):
        scratch_block = ["timeAndDate", "day of week"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catformula.FormulaElement)
        assert catr_brick.getValue() == str(catformula.Operators.PLUS)
        assert catr_brick.leftChild.getValue() == str(catformula.Sensors.DATE_WEEKDAY)
        assert catr_brick.rightChild.getValue() == str(1)

    # timeAndDate
    def test_can_convert_time_and_date_block_date(self):
        scratch_block = ["timeAndDate", "date"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catformula.FormulaElement)
        assert catr_brick.getValue() == str(catformula.Sensors.DATE_DAY)

    # timeAndDate
    def test_can_convert_time_and_date_block_month(self):
        scratch_block = ["timeAndDate", "month"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catformula.FormulaElement)
        assert catr_brick.getValue() == str(catformula.Sensors.DATE_MONTH)

    # timeAndDate
    def test_can_convert_time_and_date_block_year(self):
        scratch_block = ["timeAndDate", "year"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catformula.FormulaElement)
        assert catr_brick.getValue() == str(catformula.Sensors.DATE_YEAR)

    #putPenDown
    def test_can_convert_pen_down_block(self):
        scratch_block = ["putPenDown"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.PenDownBrick)

    #putPenUp
    def test_can_convert_pen_up_block(self):
        scratch_block = ["putPenUp"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.PenUpBrick)

    #stampCostume
    def test_can_convert_stamp_costume_block(self):
        scratch_block = ["stampCostume"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.StampBrick)

    #clearPenTrails
    def test_can_convert_clear_pen_trails_block(self):
        scratch_block = ["clearPenTrails"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ClearBackgroundBrick)

    # traverse two formula elements to check if the tree is the same
    @staticmethod
    def is_same_formula(fe1, fe2):
        if fe1 is None and fe2 is None:
            return True
        elif ((fe1 is None) != (fe2 is None)) or (fe1.getValue() != fe2.getValue()):
            return False
        return TestConvertBlocks.is_same_formula(fe1.leftChild, fe2.leftChild) and \
               TestConvertBlocks.is_same_formula(fe1.rightChild, fe2.rightChild)

    @staticmethod
    def get_color_formulas(set_color_brick):
        r = set_color_brick.getFormulaWithBrickField(catbricks.Brick.BrickField.PEN_COLOR_RED).getFormulaTree()
        g = set_color_brick.getFormulaWithBrickField(catbricks.Brick.BrickField.PEN_COLOR_GREEN).getFormulaTree()
        b = set_color_brick.getFormulaWithBrickField(catbricks.Brick.BrickField.PEN_COLOR_BLUE).getFormulaTree()
        return (r, g, b)

    # penColor: with formula (without HSV conversion algorithm compiled into bricks)
    def test_can_convert_set_pen_color_block_with_formula(self):
        test_val = catrobat.create_formula_element_for([catformula.Operators.PLUS, [42], [0]])
        scratch_block = ["penColor:", test_val]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SetPenColorBrick)

        (r, g, b) = self.get_color_formulas(catr_brick)

        assert r.getValue() == str(0)
        assert g.getValue() == str(0)
        test_fe = catrobat.create_formula_element_for([catformula.Functions.MOD, ["()", test_val], 256])
        assert TestConvertBlocks.is_same_formula(test_fe, b)

    # penColor: with string (without HSV conversion algorithm compiled into bricks)
    def test_can_convert_set_pen_color_block_with_string(self):
        color = "#adfadf"
        scratch_block = ["penColor:", color]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SetPenColorBrick)

        (r, g, b) = self.get_color_formulas(catr_brick)

        color_hex = color[1:]
        (r_check, g_check, b_check) = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))

        assert r.getValue() == str(r_check)
        assert g.getValue() == str(g_check)
        assert b.getValue() == str(b_check)

    def build_test_project(self, brick_list):
        sprite_name = "Sprite1"
        raw_json = {
            "objName": "Stage",
            "currentCostumeIndex": 0,
            "penLayerMD5": "5c81a336fab8be57adc039a8a2b33ca9.png",
            "penLayerID": 0,
            "tempoBPM": 60,
            "children": [{
                "objName": sprite_name,
                "scripts": [[107,108,[["whenGreenFlag"]] + brick_list]],
                "currentCostumeIndex": 0,
                "indexInLibrary": 1,
                "spriteInfo": {}
            }],
            "info": {}
        }

        raw_project = scratch.RawProject(raw_json)
        sprite_object = None
        for obj in raw_project.objects:
            if obj.name == sprite_name:
                sprite_object = obj
                break
        sprite = self.block_converter._catrobat_sprite_from(sprite_object, [])
        assert sprite

        catr_script = self.block_converter._catrobat_script_from(raw_project.objects[1].scripts[0], sprite, self.test_project)
        assert isinstance(catr_script, catbase.StartScript)
        return catr_script.getBrickList(), sprite, raw_project

    # helper function to test the color conversion algorithm used by penColor:, setPenParamTo: and changePenParamBy:
    @staticmethod
    def assert_hsv_to_rgb_algorithm(sprite, bricks):
        var = {}
        def var_id(variable_name):
            return catrobat.build_var_id(var[variable_name])

        def var_obj(variable_name):
            return sprite.getUserVariable(var[variable_name])

        for key, variable_name in scratch.S2CC_PEN_COLOR_HELPER_VARIABLE_NAMES.items() + \
                                  scratch.S2CC_PEN_COLOR_VARIABLE_NAMES.items():
            assert isinstance(sprite.getUserVariable(variable_name), catformula.UserVariable)
            var[key] = variable_name

        assert isinstance(bricks[0], catbricks.SetVariableBrick)
        assert bricks[0].userVariable == var_obj('h_i')
        test_fe = catrobat.create_formula_element_for(
            [catformula.Functions.FLOOR, [catformula.Operators.MULT, var_id('h'), 6]])
        assert TestConvertBlocks.is_same_formula(test_fe, bricks[0].getFormulas()[0].getFormulaTree())

        assert isinstance(bricks[1], catbricks.SetVariableBrick)
        assert bricks[1].userVariable == var_obj('f')
        test_fe = catrobat.create_formula_element_for(
            [catformula.Operators.MINUS, [catformula.Operators.MULT, var_id('h'), 6], var_id('h_i')])
        assert TestConvertBlocks.is_same_formula(test_fe, bricks[1].getFormulas()[0].getFormulaTree())

        assert isinstance(bricks[2], catbricks.SetVariableBrick)
        assert bricks[2].userVariable == var_obj('p')
        test_fe = catrobat.create_formula_element_for(
            [catformula.Operators.MULT, var_id('v'), ["()", [catformula.Operators.MINUS, 1, var_id('s')]]])
        assert TestConvertBlocks.is_same_formula(test_fe, bricks[2].getFormulas()[0].getFormulaTree())

        assert isinstance(bricks[3], catbricks.SetVariableBrick)
        assert bricks[3].userVariable == var_obj('q')
        test_fe = catrobat.create_formula_element_for(
            [catformula.Operators.MULT,
             var_id('v'),
             ["()", [catformula.Operators.MINUS, 1, [catformula.Operators.MULT, var_id('s'), var_id('f')]]]])
        assert TestConvertBlocks.is_same_formula(test_fe, bricks[3].getFormulas()[0].getFormulaTree())

        assert isinstance(bricks[4], catbricks.SetVariableBrick)
        assert bricks[4].userVariable == var_obj('t')
        test_fe = catrobat.create_formula_element_for(
            [catformula.Operators.MULT,
             var_id('v'),
             ["()", [catformula.Operators.MINUS,
                     1,
                     [catformula.Operators.MULT,
                      var_id('s'), ["()", [catformula.Operators.MINUS, 1, var_id('f')]]]]]])
        assert TestConvertBlocks.is_same_formula(test_fe, bricks[4].getFormulas()[0].getFormulaTree())

        def test_inner_bricks(if_brick, r, g, b):
            for (i, (color, name)) in enumerate([(r, 'r'), (g, 'g'), (b, 'b')]):
                brick = if_brick.ifBranchBricks[i]
                assert isinstance(brick, catbricks.SetVariableBrick)
                assert brick.userVariable == var_obj(name)
                fe_test = catrobat.create_formula_element_for(
                    [catformula.Functions.ROUND, [catformula.Operators.MULT, var_id(color), 255]])
                assert TestConvertBlocks.is_same_formula(brick.getFormulas()[0].getFormulaTree(), fe_test)

        assert isinstance(bricks[5], catbricks.IfThenLogicBeginBrick)
        test_fe = catrobat.create_formula_element_for(
            [catformula.Operators.LOGICAL_OR,
             [catformula.Operators.EQUAL, var_id('h_i'), 0],
             [catformula.Operators.EQUAL, var_id('h_i'), 6]])
        assert TestConvertBlocks.is_same_formula(test_fe, bricks[5].getFormulas()[0].getFormulaTree())
        test_inner_bricks(bricks[5], 'v', 't', 'p')

        for i in range(1, 6):
            assert isinstance(bricks[5 + i], catbricks.IfThenLogicBeginBrick)
            fe_test = catrobat.create_formula_element_for([catformula.Operators.EQUAL, var_id('h_i'), i])
            assert TestConvertBlocks.is_same_formula(fe_test, bricks[5 + i].getFormulas()[0].getFormulaTree())

        test_inner_bricks(bricks[6], 'q', 'v', 'p')
        test_inner_bricks(bricks[7], 'p', 'v', 't')
        test_inner_bricks(bricks[8], 'p', 'q', 'v')
        test_inner_bricks(bricks[9], 't', 'p', 'v')
        test_inner_bricks(bricks[10], 'v', 'p', 'q')

        assert isinstance(bricks[11], catbricks.SetPenColorBrick)
        (r, g, b) = TestConvertBlocks.get_color_formulas(bricks[11])
        for (fe, color) in [(r, 'r'), (g, 'g'), (b, 'b')]:
            fe_test = catrobat.create_formula_element_for(var_id(color))
            assert TestConvertBlocks.is_same_formula(fe_test, fe)

    # test the color conversion algorithm used by penColor:, setPenParamTo: and changePenParamBy:
    def test_hsv_to_rgb_algorithm(self):
        brick_list, sprite, raw_project = self.build_test_project([["changePenParamBy:", "color", 42]])

        workaround_info = raw_project.objects[1].preprocess_object([raw_project.objects[0].name, raw_project.objects[1].name])
        assert workaround_info[scratch.ADD_PEN_DEFAULT_BEHAVIOR]
        assert workaround_info[scratch.ADD_PEN_COLOR_VARIABLES]

        # algorithm is 12 bricks long (excluding inner bricks from e.g. if statements)
        bricks = brick_list[-12:]
        self.assert_hsv_to_rgb_algorithm(sprite, bricks)

    # penColor: with 1) string as argument 2) formula as argument. changePenParamBy: -> add conversion algorithm.
    def test_can_convert_set_pen_color_block_with_conversion_algorithm(self):
        test_val1 = "#adfadf"
        test_val2 = catrobat.create_formula_element_for([catformula.Operators.PLUS, 2, 3])

        brick_list, sprite, raw_project = self.build_test_project([["changePenParamBy:", "color", 42],
                                                                   ["penColor:", test_val2],
                                                                   ["penColor:", test_val1]])

        def assert_set_hsv_bricks(bricks, h, s, v):
            assert len(bricks) == 3
            for (brick, variable_name, variable_formula) in zip(bricks, ['h', 's', 'v'], [h, s, v]):
                assert isinstance(brick, catbricks.SetVariableBrick)
                assert brick.userVariable == sprite.getUserVariable(scratch.S2CC_PEN_COLOR_VARIABLE_NAMES[variable_name])
                test_fe = catrobat.create_formula_element_for(variable_formula)
                assert self.is_same_formula(test_fe, brick.getFormulas()[0].getFormulaTree())

        # penColor: with string as argument
        # algorithm is 12 bricks long (excluding inner bricks from e.g. if statements)
        bricks = brick_list[-12:]
        self.assert_hsv_to_rgb_algorithm(sprite, bricks)

        colors_hex = test_val1[1:]
        (r, g, b) = tuple(int(colors_hex[i:i+2], 16) for i in (0, 2, 4))
        (h, s, v) = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

        bricks = brick_list[-15:-12]
        assert_set_hsv_bricks(bricks, h, s, v)

        # penColor: with formula as argument
        bricks = brick_list[-27:-15]
        self.assert_hsv_to_rgb_algorithm(sprite, bricks)

        h = 0.66
        s = 1.0
        v = catrobat.create_formula_element_for(
            [catformula.Operators.DIVIDE, [catformula.Functions.MOD, ["()", test_val2], 256], 255.0]
        )

        bricks = brick_list[-30:-27]
        assert_set_hsv_bricks(bricks, h, s, v)

    # setPenParamTo:
    def test_can_convert_set_pen_param_to(self):
        test_val1 = 42
        test_val2 = 3.14
        test_val3 = catrobat.create_formula_element_for([catformula.Operators.MULT, 3, 4])

        brick_list, sprite, raw_project = self.build_test_project([["setPenParamTo", "transparency", 123],
                                                                   ["setPenParamTo:", "brightness", test_val3],
                                                                   ["setPenParamTo:", "saturation", test_val2],
                                                                   ["setPenParamTo:", "color", test_val1]])

        def test_bricks(bricks, affected_variable_name, test_fe):
            assert isinstance(bricks[0], catbricks.SetVariableBrick)
            assert bricks[0].userVariable == \
                   sprite.getUserVariable(scratch.S2CC_PEN_COLOR_VARIABLE_NAMES[affected_variable_name])
            assert self.is_same_formula(test_fe, bricks[0].getFormulas()[0].getFormulaTree())
            self.assert_hsv_to_rgb_algorithm(sprite, bricks[1:])

        # setPenParamTo:, "color", int
        bricks = brick_list[-13:]
        test_fe = catrobat.create_formula_element_for(
            [catformula.Functions.MOD, [catformula.Operators.DIVIDE, ["()", test_val1], 100], 1])
        test_bricks(bricks, 'h', test_fe)

        def get_test_fe(value):
            return catrobat.create_formula_element_for(
                [catformula.Functions.MAX,
                 [catformula.Functions.MIN,
                  [catformula.Operators.DIVIDE, ["()", value], 100],
                  1],
                 0])

        # setPenParamTo:, "saturation", int
        bricks = brick_list[-26:-13]
        test_fe = get_test_fe(test_val2)
        test_bricks(bricks, 's', test_fe)

        # setPenParamTo:, "brightness", formula
        bricks = brick_list[-39:-26]
        test_fe = get_test_fe(test_val3)
        test_bricks(bricks, 'v', test_fe)

        # setPenParamTo:, "transparency", int
        bricks = brick_list[-40]
        assert isinstance(bricks, catbricks.NoteBrick)

    # changePenParamBy:
    def test_can_convert_change_pen_param_by(self):
        test_val1 = 42
        test_val2 = 3.14
        test_val3 = catrobat.create_formula_element_for([catformula.Operators.MULT, 3, 4])

        brick_list, sprite, raw_project = self.build_test_project([["changePenParamBy", "transparency", 123],
                                                                   ["changePenParamBy:", "brightness", test_val3],
                                                                   ["changePenParamBy:", "saturation", test_val2],
                                                                   ["changePenParamBy:", "color", test_val1]])

        def test_bricks(bricks, affected_variable_name, test_fe):
            assert isinstance(bricks[0], catbricks.SetVariableBrick)
            assert bricks[0].userVariable == \
                   sprite.getUserVariable(scratch.S2CC_PEN_COLOR_VARIABLE_NAMES[affected_variable_name])
            assert self.is_same_formula(test_fe, bricks[0].getFormulas()[0].getFormulaTree())
            self.assert_hsv_to_rgb_algorithm(sprite, bricks[1:])

        param_name_mapping = {"color": "h", "saturation": "s", "brightness": "v"}

        # setPenParamTo:, "color", int
        bricks = brick_list[-13:]
        var_id = catrobat.build_var_id(scratch.S2CC_PEN_COLOR_VARIABLE_NAMES[param_name_mapping["color"]])
        test_fe = catrobat.create_formula_element_for(
            [catformula.Functions.MOD,
             [catformula.Operators.PLUS, var_id, [catformula.Operators.DIVIDE, ["()", test_val1], 100]],
             1])
        test_bricks(bricks, 'h', test_fe)

        def get_test_fe(var_id, value):
            return catrobat.create_formula_element_for(
                [catformula.Functions.MAX,
                 [catformula.Functions.MIN,
                  [catformula.Operators.PLUS, var_id, [catformula.Operators.DIVIDE, ["()", value], 100]],
                  1],
                 0])

        # setPenParamTo:, "saturation", int
        bricks = brick_list[-26:-13]
        var_id = catrobat.build_var_id(scratch.S2CC_PEN_COLOR_VARIABLE_NAMES[param_name_mapping["saturation"]])
        test_fe = get_test_fe(var_id, test_val2)
        test_bricks(bricks, 's', test_fe)

        # setPenParamTo:, "brightness", formula
        bricks = brick_list[-39:-26]
        var_id = catrobat.build_var_id(scratch.S2CC_PEN_COLOR_VARIABLE_NAMES[param_name_mapping["brightness"]])
        test_fe = get_test_fe(var_id, test_val3)
        test_bricks(bricks, 'v', test_fe)

        # setPenParamTo:, "transparency", int
        bricks = brick_list[-40]
        assert isinstance(bricks, catbricks.NoteBrick)

    # pen size formula check function
    @staticmethod
    def get_pen_size_formula(value):
        return catrobat.create_formula_element_for(
            [catformula.Operators.MULT, ["()", value], scratch.S2CC_PEN_SIZE_MULTIPLIER])

    # penSize: with number argument (without introducing S2CC pen size variable)
    def test_can_convert_set_pen_size_block_with_number(self):
        test_val = 42
        test_fe = self.get_pen_size_formula(test_val)
        scratch_block = ["penSize:", test_val]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SetPenSizeBrick)
        assert self.is_same_formula(test_fe, catr_brick.getFormulas()[0].getFormulaTree())

    # penSize: with formula argument (without introducing S2CC pen size variable)
    def test_can_convert_set_pen_size_block_with_formula(self):
        test_val = catrobat.create_formula_element_for([catformula.Operators.PLUS, [2], [234]])
        test_fe = self.get_pen_size_formula(test_val)
        scratch_block = ["penSize:", test_val]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.SetPenSizeBrick)
        assert self.is_same_formula(test_fe, catr_brick.getFormulas()[0].getFormulaTree())

    # changePenSizeBy: and PenSize: (checking the S2CC pen size variable)
    def can_convert_pen_size_blocks(self, test_val1, test_val2):
        brick_list, sprite, raw_project = self.build_test_project([["changePenSizeBy:", test_val1],
                                                                   ["penSize:", test_val2]])

        workaround_info = raw_project.objects[1].preprocess_object([raw_project.objects[0].name, raw_project.objects[1].name])
        assert workaround_info[scratch.ADD_PEN_DEFAULT_BEHAVIOR]
        assert workaround_info[scratch.ADD_PEN_SIZE_VARIABLE]

        # test "changePenSizeBy:"
        change_var_brick = brick_list[-4]
        size_brick = brick_list[-3]
        assert isinstance(change_var_brick, catbricks.ChangeVariableBrick)
        assert isinstance(size_brick, catbricks.SetPenSizeBrick)
        fe_test = self.get_pen_size_formula(test_val1)
        assert self.is_same_formula(fe_test, change_var_brick.getFormulas()[0].getFormulaTree())

        # test "penSize:"
        set_var_brick = brick_list[-2]
        size_brick = brick_list[-1]
        assert isinstance(set_var_brick, catbricks.SetVariableBrick)
        assert isinstance(size_brick, catbricks.SetPenSizeBrick)
        fe_test = self.get_pen_size_formula(test_val2)
        assert self.is_same_formula(fe_test, set_var_brick.getFormulas()[0].getFormulaTree())

    # changePenSizeBy: and PenSize: with numbers (checking the S2CC pen size variable)
    def test_can_convert_pen_size_blocks_with_numbers(self):
        self.can_convert_pen_size_blocks(3.14, 2.0)

    # changePenSizeBy: and PenSize: with formulas (checking the S2CC pen size variable)
    def test_can_convert_pen_size_blocks_with_formulas(self):
        test_val1 = catrobat.create_formula_element_for([catformula.Operators.MULT, 3.14, 2])
        test_val2 = catrobat.create_formula_element_for([catformula.Functions.MOD, 455.4, 22])
        self.can_convert_pen_size_blocks(test_val1, test_val2)

    def test_can_convert_set_variable_with_list(self):
        variable_name = "test_var"
        project = self.block_converter._catrobat_project
        catrobat.add_user_variable(project, variable_name, DUMMY_CATR_SPRITE, DUMMY_CATR_SPRITE.getName())
        scratch_block = ["setVar:to:", "test_var", ["contentsOfList:", self._name_of_test_list]]
        catr_bricks = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_bricks[0], catbricks.SetVariableBrick)
        assert catr_bricks[0].getFormulas()[0].getFormulaTree().getElementType() == catElementType.USER_LIST
        assert catr_bricks[0].getFormulas()[0].getFormulaTree().getValue() == self._name_of_test_list

    # TODO: uncomment these tests as soon as Catrobat supports user bricks again.
    # Note: these tests might have to be refactored together with the tested function.
    '''
    #call
    def test_can_convert_call_block_user_script_already_defined_simple(self):
        function_header = "number1 %n number1"
        expected_param_label = "param1"
        expected_param_value = 1
        scratch_block = ["call", function_header, expected_param_value]

        scratch_user_script_declared_labels_map = { function_header: [expected_param_label] }
        sprite_context = converter.SpriteContext(DUMMY_CATR_SPRITE.getName(), scratch_user_script_declared_labels_map)
        script_context = converter.ScriptContext(sprite_context)
        catr_bricks = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE, script_context)

        assert len(catr_bricks) == 1
        assert isinstance(catr_bricks[0], catbricks.UserBrick)
        user_brick = catr_bricks[0]

        definition_brick = user_brick.getDefinitionBrick()
        assert definition_brick is not None
        assert isinstance(definition_brick, catbricks.UserScriptDefinitionBrick)
        assert definition_brick.getUserScript() is not None
        assert isinstance(definition_brick.getUserScript(), catbase.StartScript)

        definition_brick_elements = definition_brick.getUserScriptDefinitionBrickElements()
        assert len(definition_brick_elements) == 3
        assert isinstance(definition_brick_elements[0], catbricks.UserScriptDefinitionBrickElement)
        assert definition_brick_elements[0].isText()
        assert definition_brick_elements[0].getText() == "number1"
        assert isinstance(definition_brick_elements[1], catbricks.UserScriptDefinitionBrickElement)
        assert definition_brick_elements[1].isVariable()
        assert isinstance(definition_brick_elements[2], catbricks.UserScriptDefinitionBrickElement)
        assert definition_brick_elements[2].isText()
        assert definition_brick_elements[2].getText() == "number1"

        user_brick_params = user_brick.getUserBrickParameters()
        assert len(user_brick_params) == 1
        assert isinstance(user_brick_params[0], catbricks.UserBrickParameter)
        assert user_brick == user_brick_params[0].getParent()

        formula_tree = user_brick_params[0].getFormulaWithBrickField(catbasebrick.BrickField.USER_BRICK).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.NUMBER == formula_tree.type
        assert str(expected_param_value) == formula_tree.value
        assert formula_tree.leftChild is None
        assert formula_tree.rightChild is None

        user_script_definition_brick = sprite_context.user_script_definition_brick_map[function_header]
        assert user_script_definition_brick is not None
        assert isinstance(user_script_definition_brick, catbricks.UserScriptDefinitionBrick)

        param_types = sprite_context.user_script_params_map[function_header]
        assert param_types is not None
        assert isinstance(param_types, list)
        assert len(param_types) == 1
        assert param_types[0] == "%n"

    #call
    def test_can_convert_call_block_user_script_already_defined_complex(self):
        function_header = "number1 %n string1 %s boolean1 %b"
        expected_first_param_label = "param1"
        expected_first_param_value = expected_first_param_operator, expected_first_param_left_operand, \
                                     expected_first_param_right_operand = ["+", 1, 2]
        expected_second_param_label = "param2"
        expected_second_param_value = "This is a message"
        expected_third_param_label = "param3"
        expected_third_param_value = True
        scratch_block = ["call", function_header, expected_first_param_value, expected_second_param_value, expected_third_param_value]

        scratch_user_script_declared_labels_map = {
            function_header: [
                expected_first_param_label,
                expected_second_param_label,
                expected_third_param_label
            ]
        }
        sprite_context = converter.SpriteContext(DUMMY_CATR_SPRITE.getName(), scratch_user_script_declared_labels_map)
        script_context = converter.ScriptContext(sprite_context)
        catr_bricks = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE, script_context)

        assert len(catr_bricks) == 1
        assert isinstance(catr_bricks[0], catbricks.UserBrick)
        user_brick = catr_bricks[0]

        definition_brick = user_brick.getDefinitionBrick()
        assert definition_brick is not None
        assert isinstance(definition_brick, catbricks.UserScriptDefinitionBrick)
        assert definition_brick.getUserScript() is not None
        assert isinstance(definition_brick.getUserScript(), catbase.StartScript)

        definition_brick_elements = definition_brick.getUserScriptDefinitionBrickElements()
        assert len(definition_brick_elements) == 6
        assert isinstance(definition_brick_elements[0], catbricks.UserScriptDefinitionBrickElement)
        assert definition_brick_elements[0].isText()
        assert definition_brick_elements[0].getText() == "number1"
        assert isinstance(definition_brick_elements[1], catbricks.UserScriptDefinitionBrickElement)
        assert definition_brick_elements[1].isVariable()
        assert isinstance(definition_brick_elements[2], catbricks.UserScriptDefinitionBrickElement)
        assert definition_brick_elements[2].isText()
        assert definition_brick_elements[2].getText() == "string1"
        assert isinstance(definition_brick_elements[3], catbricks.UserScriptDefinitionBrickElement)
        assert definition_brick_elements[3].isVariable()
        assert isinstance(definition_brick_elements[4], catbricks.UserScriptDefinitionBrickElement)
        assert definition_brick_elements[4].isText()
        assert definition_brick_elements[4].getText() == "boolean1"
        assert isinstance(definition_brick_elements[5], catbricks.UserScriptDefinitionBrickElement)
        assert definition_brick_elements[5].isVariable()

        user_brick_params = user_brick.getUserBrickParameters()
        assert len(user_brick_params) == 3
        assert isinstance(user_brick_params[0], catbricks.UserBrickParameter)
        assert user_brick == user_brick_params[0].getParent()
        assert isinstance(user_brick_params[1], catbricks.UserBrickParameter)
        assert user_brick == user_brick_params[1].getParent()
        assert isinstance(user_brick_params[2], catbricks.UserBrickParameter)
        assert user_brick == user_brick_params[2].getParent()

        formula_tree = user_brick_params[0].getFormulaWithBrickField(catbasebrick.BrickField.USER_BRICK).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.OPERATOR == formula_tree.type
        assert formula_tree.value == catformula.Operators.PLUS.toString() # @UndefinedVariable
        assert formula_tree.leftChild is not None
        assert formula_tree.rightChild is not None

        formula_left_child = formula_tree.leftChild
        assert formula_left_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_first_param_left_operand) == formula_left_child.value
        assert formula_left_child.leftChild is None
        assert formula_left_child.rightChild is None

        formula_right_child = formula_tree.rightChild
        assert formula_right_child.type == catformula.FormulaElement.ElementType.NUMBER
        assert str(expected_first_param_right_operand) == formula_right_child.value
        assert formula_right_child.leftChild is None
        assert formula_right_child.rightChild is None

        formula_tree = user_brick_params[1].getFormulaWithBrickField(catbasebrick.BrickField.USER_BRICK).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.STRING == formula_tree.type
        assert str(expected_second_param_value) == formula_tree.value
        assert formula_tree.leftChild is None
        assert formula_tree.rightChild is None

        formula_tree = user_brick_params[2].getFormulaWithBrickField(catbasebrick.BrickField.USER_BRICK).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.NUMBER == formula_tree.type
        assert str(int(expected_third_param_value)) == formula_tree.value
        assert formula_tree.leftChild is None
        assert formula_tree.rightChild is None

        user_script_definition_brick = sprite_context.user_script_definition_brick_map[function_header]
        assert user_script_definition_brick is not None
        assert isinstance(user_script_definition_brick, catbricks.UserScriptDefinitionBrick)

        param_types = sprite_context.user_script_params_map[function_header]
        assert param_types is not None
        assert isinstance(param_types, list)
        assert len(param_types) == 3
        assert param_types[0] == "%n"
        assert param_types[1] == "%s"
        assert param_types[2] == "%b"

    #call
    def test_can_convert_call_block_user_script_not_yet_defined_simple(self):
        function_header = "number1 %n number1"
        expected_param_label = "param1"
        expected_param_value = 1
        scratch_block = ["call", function_header, expected_param_value]

        expected_user_script_definition_brick = catbricks.UserScriptDefinitionBrick()
        user_script_definition_brick_elements_list = expected_user_script_definition_brick.getUserScriptDefinitionBrickElements()

        first_user_script_definition_brick_element = catbricks.UserScriptDefinitionBrickElement()
        first_user_script_definition_brick_element.setIsText()
        first_user_script_definition_brick_element.setText("number1")
        user_script_definition_brick_elements_list.add(first_user_script_definition_brick_element)

        second_user_script_definition_brick_element = catbricks.UserScriptDefinitionBrickElement()
        second_user_script_definition_brick_element.setIsVariable()
        second_user_script_definition_brick_element.setText(expected_param_label)
        user_script_definition_brick_elements_list.add(second_user_script_definition_brick_element)

        third_user_script_definition_brick_element = catbricks.UserScriptDefinitionBrickElement()
        third_user_script_definition_brick_element.setIsText()
        third_user_script_definition_brick_element.setText("number1")
        user_script_definition_brick_elements_list.add(third_user_script_definition_brick_element)

        expected_param_types = ["%n"]
        scratch_user_script_declared_labels_map = { function_header: [expected_param_label] }
        sprite_context = converter.SpriteContext(DUMMY_CATR_SPRITE.getName(), scratch_user_script_declared_labels_map)
        sprite_context.user_script_definition_brick_map[function_header] = expected_user_script_definition_brick
        sprite_context.user_script_params_map[function_header] = expected_param_types
        script_context = converter.ScriptContext(sprite_context)
        catr_bricks = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE, script_context)

        assert len(catr_bricks) == 1
        assert isinstance(catr_bricks[0], catbricks.UserBrick)
        user_brick = catr_bricks[0]

        definition_brick = user_brick.getDefinitionBrick()
        assert definition_brick is not None
        assert isinstance(definition_brick, catbricks.UserScriptDefinitionBrick)
        assert definition_brick.getUserScript() is not None
        assert isinstance(definition_brick.getUserScript(), catbase.StartScript)

        definition_brick_elements = definition_brick.getUserScriptDefinitionBrickElements()
        assert len(definition_brick_elements) == 3
        assert id(first_user_script_definition_brick_element) == id(definition_brick_elements[0])
        assert id(second_user_script_definition_brick_element) == id(definition_brick_elements[1])
        assert id(third_user_script_definition_brick_element) == id(definition_brick_elements[2])

        user_brick_params = user_brick.getUserBrickParameters()
        assert len(user_brick_params) == 1
        assert isinstance(user_brick_params[0], catbricks.UserBrickParameter)
        assert user_brick == user_brick_params[0].getParent()

        formula_tree = user_brick_params[0].getFormulaWithBrickField(catbasebrick.BrickField.USER_BRICK).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.NUMBER == formula_tree.type
        assert str(expected_param_value) == formula_tree.value
        assert formula_tree.leftChild is None
        assert formula_tree.rightChild is None

        user_script_definition_brick = sprite_context.user_script_definition_brick_map[function_header]
        assert user_script_definition_brick is not None
        assert id(expected_user_script_definition_brick) == id(user_script_definition_brick)

        param_types = sprite_context.user_script_params_map[function_header]
        assert param_types is not None
        assert expected_param_types == param_types
    '''

    #gotoSpriteOrMouse:
    def test_can_convert_go_to_sprite_block_with_sprite_afterwards(self):
        test_sprite_name = "Afterwards"
        scratch_block = ["gotoSpriteOrMouse:", test_sprite_name]
        context = converter.Context()
        sprite_context = converter.SpriteContext(DUMMY_CATR_SPRITE.getName(), {})
        sprite_context.context = context
        script_context = converter.ScriptContext(sprite_context)
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE, script_context)
        assert isinstance(catr_brick, catbricks.GoToBrick)
        assert catr_brick.destinationSprite.getName() == test_sprite_name
        assert "Afterwards" in context.upcoming_sprites
        assert catr_brick.destinationSprite is context.upcoming_sprites["Afterwards"]

    #gotoSpriteOrMouse:
    def test_can_convert_go_to_sprite_block_with_sprite_previous(self):
        test_sprite_name = "Previous"
        scratch_block = ["gotoSpriteOrMouse:", test_sprite_name]
        sprite_object = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, "Previous")
        self.test_scene.spriteList.append(sprite_object)
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.GoToBrick)
        assert catr_brick.destinationSprite.getName() == test_sprite_name
        assert catr_brick.destinationSprite is sprite_object

    #gotoSpriteOrMouse:
    def test_can_convert_go_to_sprite_block_with_random_position(self):
        test_sprite_name = "_random_"
        scratch_block = ["gotoSpriteOrMouse:", test_sprite_name]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.PlaceAtBrick)
        [x_formula, y_formula] = catr_brick.getFormulas()
        assert(x_formula.getFormulaTree().value == str(catformula.Functions.RAND))
        assert(y_formula.getFormulaTree().value == str(catformula.Functions.RAND))

    #pointTowards:
    def test_can_convert_point_towards_block_basic(self):
        test_sprite_name = "spr"
        scratch_block = ["pointTowards:", test_sprite_name]
        context = converter.Context()
        sprite_context = converter.SpriteContext(DUMMY_CATR_SPRITE.getName())
        sprite_context.context = context
        script_context = converter.ScriptContext(sprite_context)

        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE, script_context)
        assert isinstance(catr_brick, catbricks.PointToBrick)
        assert catr_brick.pointedObject.name == "spr"

        #pointTowards:
    def test_can_convert_point_towards_block_mouse(self):
        test_sprite_name = "_mouse_"
        scratch_block = ["pointTowards:", test_sprite_name]
        context = converter.Context()
        sprite_context = converter.SpriteContext(DUMMY_CATR_SPRITE.getName())
        sprite_context.context = context
        script_context = converter.ScriptContext(sprite_context)

        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE, script_context)

        assert isinstance(catr_brick, catbricks.PointToBrick)
        assert catr_brick.pointedObject.name == "_mouse_"
        assert "_mouse_" in context.upcoming_sprites
        assert catr_brick.pointedObject is context.upcoming_sprites["_mouse_"]

        #pointTowards:
    def test_can_convert_point_towards_block_existing_sprite(self):
        test_sprite_name = "test_sprite"
        scratch_block = ["pointTowards:", test_sprite_name]
        sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, test_sprite_name)
        self.test_scene.addSprite(sprite)

        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)

        assert isinstance(catr_brick, catbricks.PointToBrick)
        assert catr_brick.pointedObject.name == test_sprite_name

    #sceneName
    def test_can_convert_backdrop_name_block(self):
        scratch_block = ["sceneName"]
        [formula] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(formula, catformula.FormulaElement)
        assert formula.value == "OBJECT_BACKGROUND_NAME"

    #backgroundIndex
    def test_can_convert_background_index_block(self):
        scratch_block = ["backgroundIndex"]
        [formula] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(formula, catformula.FormulaElement)
        assert formula.value == "OBJECT_BACKGROUND_NUMBER"

    #costumeIndex
    def test_can_convert_costume_index_block(self):
        scratch_block = ["costumeIndex"]
        [formula] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(formula, catformula.FormulaElement)
        assert formula.value == "OBJECT_LOOK_NUMBER"

    #scale
    def test_can_convert_size_block(self):
        scratch_block = ["scale"]
        [formula] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(formula, catformula.FormulaElement)
        assert formula.value == "OBJECT_SIZE"

    #dragMode
    def test_can_convert_dragmode_block(self):
        sprite = create_catrobat_sprite_stub()
        num_scripts = len(sprite.getScriptList())

        scratch_block = ["dragMode", "draggable"]
        [setBrick] = self.block_converter._catrobat_bricks_from(scratch_block, sprite)
        assert setBrick.getUserVariable().getName() == "draggable"
        assert len(setBrick.getFormulas()) == 1
        assert setBrick.getFormulas()[0].getFormulaTree().getValue() == "TRUE"
        assert setBrick.getFormulas()[0].getFormulaTree().getElementType() == catElementType.FUNCTION
        assert isinstance(setBrick, catbricks.SetVariableBrick)
        assert len(sprite.getScriptList()) == num_scripts+1

        scratch_block = ["dragMode", "not draggable"]
        [setBrick] = self.block_converter._catrobat_bricks_from(scratch_block, sprite)
        assert(setBrick.getUserVariable().getName() == "draggable")
        assert(len(setBrick.getFormulas()) == 1)
        assert(setBrick.getFormulas()[0].getFormulaTree().getValue() == "FALSE")
        assert(setBrick.getFormulas()[0].getFormulaTree().getElementType() == catElementType.FUNCTION)
        assert isinstance(setBrick, catbricks.SetVariableBrick)
        assert len(sprite.getScriptList()) == num_scripts+1

    def test_can_convert_key_pressed_block(self):
        objectJson = {
            "objName": "Sprite1",
            "scripts": [[107,108,[["whenGreenFlag"],
                                  ["doForever",
                                   [["doIf", ["keyPressed:", "w"],
                                     [["changeYposBy:", 1]]]]]]]],
            "currentCostumeIndex": 0,
            "indexInLibrary": 1,
            "spriteInfo": {}
        }
        obj = scratch.Object(objectJson)
        workaround_info = obj.preprocess_object([obj.name])
        assert len(workaround_info[scratch.ADD_KEY_PRESSED_SCRIPT_KEY]) == 1

        raw_json = {
            "objName": "Stage",
            "currentCostumeIndex": 0,
            "penLayerMD5": "5c81a336fab8be57adc039a8a2b33ca9.png",
            "penLayerID": 0,
            "tempoBPM": 60,
            "children": [{
                "objName": "Sprite1",
                "scripts": [[107,108,[["whenGreenFlag"],
                                      ["doForever",
                                       [["doIf", ["keyPressed:", "w"],
                                         [["changeYposBy:", 1]]]]]]]],
                "currentCostumeIndex": 0,
                "indexInLibrary": 1,
                "spriteInfo": {}
            }],
            "info": {}
        }

        raw_project = scratch.RawProject(raw_json)
        catr_script = self.block_converter._catrobat_script_from(raw_project.objects[1].scripts[0], DUMMY_CATR_SPRITE, self.test_project)
        assert isinstance(catr_script, catbase.StartScript)
        brick_list = catr_script.getBrickList()
        if_brick = brick_list[0].loopBricks[0]
        assert isinstance(if_brick, catbricks.IfThenLogicBeginBrick)
        assert len(if_brick.formulaMap) == 1
        assert if_brick.formulaMap[catbricks.Brick.BrickField.IF_CONDITION] != None
        key_pressed_condition = if_brick.formulaMap[catbricks.Brick.BrickField.IF_CONDITION]
        assert isinstance(key_pressed_condition, catformula.Formula)
        key_pressed_condition_formula_tree = key_pressed_condition.formulaTree
        assert key_pressed_condition_formula_tree.value == "S2CC:key_w"
        assert key_pressed_condition_formula_tree.type == catElementType.USER_VARIABLE
        #If the addition of keys works, the addition of keys also works for this workaround. (Is tested separately.

class TestConvertedProjectAppendedKeySpriteScripts(common_testing.ProjectTestCase):
    def _load_test_scratch_project(self, project_name):
        if os.path.splitext(project_name)[1]:
            tempdir = common.TemporaryDirectory()
            scratch_project_dir = tempdir.name
            self.addCleanup(tempdir.cleanup)
            common.extract(common_testing.get_test_project_packed_file(project_name),
                           scratch_project_dir)
        else:
            scratch_project_dir = common_testing.get_test_project_path(project_name)

        scratch_project = scratch.Project(scratch_project_dir, name=project_name,
                                          project_id=common_testing.PROJECT_DUMMY_ID)
        return scratch_project

    def test_key_pressed_block(self):
        project_name = 'key_pressed_block'
        scratch_project = self._load_test_scratch_project(project_name)
        context = converter.Context()
        converted_project = converter.converted(scratch_project, None, context)

        default_scene = converted_project.catrobat_program.getDefaultScene()
        assert len(default_scene.spriteList) == 5

        key_tilt = default_scene.spriteList[2]
        assert key_tilt is not None
        assert key_tilt.name == 'key_tilt_none'

        tilt_scripts = key_tilt.getScriptList()
        assert len(tilt_scripts) == 10
        assert isinstance(tilt_scripts[1], catbase.WhenScript)

        key_row4_visibility = default_scene.spriteList[3]
        assert key_row4_visibility is not None
        assert key_row4_visibility.name == 'key_row4_visibility'

        hide_scripts = key_row4_visibility.getScriptList()
        assert len(hide_scripts) == 2
        assert isinstance(hide_scripts[1], catbase.WhenScript)

        key_w = default_scene.spriteList[4]
        assert key_w is not None
        assert key_w.name == 'key_w'

        scripts = key_w.getScriptList()
        assert len(scripts) == 3
        assert isinstance(scripts[1], catbase.WhenScript)

        brick_list = scripts[1].getBrickList()
        assert len(brick_list) == 3

        set_variable_initial = brick_list[0]
        assert isinstance(set_variable_initial, catbricks.SetVariableBrick)
        assert set_variable_initial.getUserVariable().name == 'S2CC:key_w'
        assert set_variable_initial.formulaMap[catbricks.Brick.BrickField.VARIABLE] != None

        set_variable_initial_formula = set_variable_initial.formulaMap[catbricks.Brick.BrickField.VARIABLE]
        set_variable_initial_formula_tree = set_variable_initial_formula.formulaTree
        assert set_variable_initial_formula_tree.value == str(1)
        assert set_variable_initial_formula_tree.type == catElementType.NUMBER

        wait_until_brick = brick_list[1]
        assert isinstance(wait_until_brick, catbricks.WaitUntilBrick)
        assert wait_until_brick.formulaMap[catbricks.Brick.BrickField.IF_CONDITION] != None

        wait_until_brick_formula = wait_until_brick.formulaMap[catbricks.Brick.BrickField.IF_CONDITION]
        wait_until_brick_formula_tree = wait_until_brick_formula.formulaTree
        assert wait_until_brick_formula_tree.value == 'LOGICAL_NOT'
        assert wait_until_brick_formula_tree.type == catElementType.OPERATOR
        assert wait_until_brick_formula_tree.rightChild.value == 'COLLIDES_WITH_FINGER'
        assert wait_until_brick_formula_tree.rightChild.type == catElementType.SENSOR

        set_variable_notpressed = brick_list[2]
        assert isinstance(set_variable_notpressed, catbricks.SetVariableBrick)
        assert set_variable_notpressed.getUserVariable().name == 'S2CC:key_w'
        assert set_variable_notpressed.formulaMap[catbricks.Brick.BrickField.VARIABLE] != None

        set_variable_notpressed_formula = set_variable_notpressed.formulaMap[catbricks.Brick.BrickField.VARIABLE]
        set_variable_notpressed_formula_tree = set_variable_notpressed_formula.formulaTree
        assert set_variable_notpressed_formula_tree.value == str(0.0)
        assert set_variable_notpressed_formula_tree.type == catElementType.NUMBER

        catrobat_zip_file_name = converted_project.save_as_catrobat_package_to(self._testresult_folder_path)
        self.assertValidCatrobatProgramPackageAndUnpackIf(catrobat_zip_file_name, project_name,
                                                          unused_scratch_resources=scratch_project.unused_resource_names)

    def test_key_pressed_script(self):
        project_name = 'key_pressed_script'
        scratch_project = self._load_test_scratch_project(project_name)
        context = converter.Context()
        converted_project = converter.converted(scratch_project, None, context)

        default_scene = converted_project.catrobat_program.getDefaultScene()
        assert len(default_scene.spriteList) == 4

        sprite = default_scene.spriteList[1]
        assert sprite is not None
        assert sprite.name == 'Sprite1'

        spritescripts = sprite.getScriptList()
        assert len(spritescripts) == 2

        broadcast_script = spritescripts[1]
        assert isinstance(broadcast_script, catbase.BroadcastScript)
        assert broadcast_script.getBroadcastMessage() == 'key_space_pressed'

        sprite_brick_list = spritescripts[1].getBrickList()
        assert len(sprite_brick_list) == 1

        move_brick = sprite_brick_list[0]
        assert isinstance(move_brick, catbricks.MoveNStepsBrick)

        key_row1_visibility = default_scene.spriteList[2]
        assert key_row1_visibility is not None
        assert key_row1_visibility.name == 'key_row1_visibility'

        hide_scripts = key_row1_visibility.getScriptList()
        assert len(hide_scripts) == 2
        assert isinstance(hide_scripts[1], catbase.WhenScript)

        key_space = default_scene.spriteList[3]
        assert key_space is not None
        assert key_space.name == 'key_space'

        keyscripts = key_space.getScriptList()
        assert len(keyscripts) == 3
        assert isinstance(keyscripts[1], catbase.WhenScript)

        key_brick_list = keyscripts[1].getBrickList()
        assert len(key_brick_list) == 3

        broadcast_brick = key_brick_list[0]
        assert isinstance(broadcast_brick, catbricks.BroadcastBrick)
        assert broadcast_brick.getBroadcastMessage() == 'key_space_pressed'


class TestConvertProjects(common_testing.ProjectTestCase):
    def _load_test_scratch_project(self, project_name, force_download=False):
        if (not force_download and os.path.exists("test/res/scratch/"+project_name)):
            is_local_project = True

        scratch_project_dir = common_testing.get_test_project_path(project_name)
        isScratch3Project = scratch3.is_scratch3_project(scratch_project_dir)
        if isScratch3Project:
            scratch3.convert_to_scratch2_data(scratch_project_dir, 0)

        scratch_project = scratch.Project(scratch_project_dir, name=project_name,
                                          project_id=common_testing.PROJECT_DUMMY_ID, is_local_project=is_local_project)
        return scratch_project

    def _test_project(self, project_name):
        scratch_project = self._load_test_scratch_project(project_name)
        context = converter.Context()
        converted_project = converter.converted(scratch_project, None, context)
        catrobat_zip_file_name = converted_project.save_as_catrobat_package_to(self._testresult_folder_path)
        self.assertValidCatrobatProgramPackageAndUnpackIf(catrobat_zip_file_name, project_name,
                                                          unused_scratch_resources=scratch_project.unused_resource_names)
        return converted_project.catrobat_program

    def _setup_media_converter(self):
        project_name = 'key_pressed_block'
        scratch_project = self._load_test_scratch_project(project_name)
        catrobat_program = self._test_project("key_pressed_block")
        with common.TemporaryDirectory() as catrobat_program_dir:
            sounds_path = os.path.join(catrobat_program_dir, "Scene 1", "sounds")
            os.makedirs(sounds_path)
            images_path = os.path.join(catrobat_program_dir, "Scene 1", "images")
            os.makedirs(images_path)
            for _ in (catrobat_program_dir, sounds_path, images_path):
                open(os.path.join(_, catrobat.ANDROID_IGNORE_MEDIA_MARKER_FILE_NAME), 'a').close()
        media_converter = mediaconverter.MediaConverter(scratch_project, catrobat_program,
                                                        images_path, sounds_path)
        return media_converter

    def _setup_media_converter_unconverted_media_resources(self, media_converter):
        progress_bar = None
        for scratch_object in media_converter.scratch_project.objects:
            media_converter.setup_costume_info(scratch_object,
                                               progress_bar)

    def _setup_media_converter_new_src_path(self, media_converter):
        self._setup_media_converter_unconverted_media_resources(media_converter)
        return media_converter.conversion_svgtopng_wav(None)

    def _setup_media_converter_all_used_resources(self, media_converter):
        progress_bar = None

        for scratch_object in media_converter.scratch_project.objects:
            media_converter.setup_costume_info(scratch_object,
                                               progress_bar)
        for scratch_object in media_converter.scratch_project.objects:
            media_converter.setup_sound_info(scratch_object,
                                             progress_bar)



    def test_media_converter_setup_costume_info(self):
        media_converter = self._setup_media_converter()
        progress_bar = None

        for scratch_object in media_converter.scratch_project.objects:
            media_converter.setup_costume_info(scratch_object,
                                               progress_bar)

        assert progress_bar is None
        assert not media_converter.resources.converted_media_resources_paths
        assert len(media_converter.resources.unconverted_media_resources)
        for val in media_converter.resources.unconverted_media_resources:
            assert val['media_type'] == 3
        assert len(media_converter.resources.all_used_resources)

    def test_media_converter_setup_sound_info(self):
        media_converter = self._setup_media_converter()
        progress_bar = None

        for scratch_object in media_converter.scratch_project.objects:
            media_converter.setup_sound_info(scratch_object,
                                             progress_bar)
        assert progress_bar is None
        assert not media_converter.resources.converted_media_resources_paths
        #since it is android_compatible_wav
        assert len(media_converter.resources.unconverted_media_resources) == 0
        assert len(media_converter.resources.all_used_resources)

    def test_media_converter_setup_resource_info_dict_costume(self):
        progress_bar = None
        media_converter = self._setup_media_converter()
        threads = []
        defined_scratch_object = media_converter.scratch_project.objects[0]
        costume_info = defined_scratch_object.get_costumes()[0]
        costume_dict = media_converter.get_info(costume_info["baseLayerMD5"])
        assert os.path.exists(costume_dict["src_path"]), "Not existing: {}".format(costume_dict["src_path"])
        assert costume_dict["file_ext"] in {".png", ".svg", ".jpg", ".gif"}, \
            "Unsupported image file extension: %s" % costume_dict["src_path"]
        ispng = costume_dict["file_ext"] == ".png"
        is_unconverted = costume_dict["file_ext"] == ".svg"
        media_converter.setup_resource_info_dict(costume_dict["file_name"], costume_dict["src_path"], is_unconverted, costume_info,
                                                 progress_bar, threads, ispng, True)
        assert progress_bar is None
        assert not media_converter.resources.converted_media_resources_paths
        assert len(media_converter.resources.unconverted_media_resources) == 0
        assert len(media_converter.resources.all_used_resources)

    def test_media_converter_setup_resource_info_dict_sound(self):
        progress_bar = None
        media_converter = self._setup_media_converter()
        defined_scratch_object = media_converter.scratch_project.objects[0]
        sound_info = defined_scratch_object.get_sounds()[0]
        sound_dict = media_converter.get_info(sound_info["md5"])
        assert os.path.exists(sound_dict["src_path"]), "Not existing: {}".format(sound_dict["src_path"])
        assert sound_dict["file_ext"] in {".wav", ".mp3"}, "Unsupported sound file extension: %s" % sound_dict["src_path"]
        is_unconverted = sound_dict["file_ext"] == ".wav" and not wavconverter.is_android_compatible_wav(sound_dict["src_path"])
        media_converter.setup_resource_info_dict(sound_dict["file_name"], sound_dict["src_path"], is_unconverted, sound_info,
                                                 progress_bar, [])
        assert progress_bar is None
        assert not media_converter.resources.converted_media_resources_paths
        assert len(media_converter.resources.unconverted_media_resources) == 0
        assert len(media_converter.resources.all_used_resources)

    def test_media_converter_get_info(self):
        media_converter = self._setup_media_converter()
        defined_scratch_object = media_converter.scratch_project.objects[0]
        costume_info = defined_scratch_object.get_costumes()[0]
        costume_dict = media_converter.get_info(costume_info["baseLayerMD5"])
        assert os.path.exists(costume_dict["src_path"]), "Not existing: {}".format(costume_dict["src_path"])
        assert costume_dict["file_ext"] in {".png", ".svg", ".jpg", ".gif"}, \
            "Unsupported image file extension: %s" % costume_dict["src_path"]

        sound_info = defined_scratch_object.get_sounds()[0]
        sound_dict = media_converter.get_info(sound_info["md5"])
        assert os.path.exists(sound_dict["src_path"]), "Not existing: {}".format(sound_dict["src_path"])
        assert sound_dict["file_ext"] in {".wav", ".mp3"}, "Unsupported sound file extension: %s" % sound_dict["src_path"]

    def test_media_converter_conversion_svgtopng_wav(self):
        media_converter = self._setup_media_converter()
        self._setup_media_converter_unconverted_media_resources(media_converter)
        new_src_paths = media_converter.conversion_svgtopng_wav(None)
        assert len(new_src_paths) > 0

    def test_resource_info_setup(self):
        media_converter = self._setup_media_converter()
        test_new_src_path = self._setup_media_converter_new_src_path(media_converter)
        duplicate_filename_set = set()
        media_converter.resource_info_setup(duplicate_filename_set, test_new_src_path)
        assert len(media_converter.resources.converted_media_resources_paths) > 0

    def _test_mouse_pointer_tracking_workaround(self, catrobat_program):
        scene = catrobat_program.getDefaultScene()
        sprite_list = scene.getSpriteList()

        # check if the 'distanceTo'- or 'glideTo'-brick with the mouse-pointer as target
        # was converted correctly -> workaround for this brick is realized during
        # conversion and needs a scratch.Project() constructor to be tested -> testing this
        # in a earlier phase not possible
        mouse_sprite = sprite_list[-1]
        assert mouse_sprite.name == "_mouse_"

        mouse_sprite_script_list = mouse_sprite.scriptList
        assert len(mouse_sprite_script_list) == 4

        position_tracking_script = mouse_sprite_script_list[0]
        go_to_touch_position_script = mouse_sprite_script_list[1]
        touch_screen_detection_script = mouse_sprite_script_list[2]
        create_clone_at_touch_position_script = mouse_sprite_script_list[3]

        assert isinstance(position_tracking_script, catbase.StartScript)
        assert isinstance(go_to_touch_position_script, catbase.BroadcastScript)
        assert isinstance(touch_screen_detection_script, catbase.StartScript)
        assert isinstance(create_clone_at_touch_position_script, catbase.WhenClonedScript)

        assert len(position_tracking_script.brickList) == 1
        assert len(go_to_touch_position_script.brickList) == 1
        assert len(touch_screen_detection_script.brickList) == 2
        assert len(create_clone_at_touch_position_script.brickList) == 3

        forever_brick = position_tracking_script.brickList[0]
        assert isinstance(forever_brick, catbricks.ForeverBrick)
        assert len(forever_brick.loopBricks) == 3
        assert isinstance(forever_brick.loopBricks[0], catbricks.SetVariableBrick)
        assert isinstance(forever_brick.loopBricks[1], catbricks.SetVariableBrick)
        assert isinstance(forever_brick.loopBricks[2], catbricks.WaitBrick)

        go_to_brick = go_to_touch_position_script.brickList[0]
        assert isinstance(go_to_brick, catbricks.GoToBrick)
        assert go_to_brick.spinnerSelection == catcommon.BrickValues.GO_TO_TOUCH_POSITION

        set_transparency_brick = touch_screen_detection_script.brickList[0]
        forever_brick = touch_screen_detection_script.brickList[1]
        assert isinstance(set_transparency_brick, catbricks.SetTransparencyBrick)
        assert isinstance(forever_brick, catbricks.ForeverBrick)

        go_to_brick = create_clone_at_touch_position_script.brickList[0]
        if_then_logic_brick = create_clone_at_touch_position_script.brickList[1]
        delete_this_clone_brick = create_clone_at_touch_position_script.brickList[2]
        assert isinstance(go_to_brick, catbricks.GoToBrick)
        assert go_to_brick.spinnerSelection == catcommon.BrickValues.GO_TO_TOUCH_POSITION
        assert isinstance(if_then_logic_brick, catbricks.IfThenLogicBeginBrick)
        assert len(if_then_logic_brick.ifBranchBricks) == 1
        broadcast_brick = if_then_logic_brick.ifBranchBricks[0]
        assert isinstance(broadcast_brick, catbricks.BroadcastBrick)
        assert isinstance(delete_this_clone_brick, catbricks.DeleteThisCloneBrick)

    # Checks if the visible global or local variables in the scratch program are converted into show test bricks in the converted project
    def test_can_convert_visible_variables(self):
        scratch_project = self._load_test_scratch_project("visible_variables")
        catrobat_program = self._test_project("visible_variables")
        scene = catrobat_program.getDefaultScene()
        sprite_dict = {}
        sprite_list = scene.getSpriteList()
        for sprite in sprite_list:
            sprite_name = sprite.getName()
            sprite_name = sprite_name.replace(BACKGROUND_LOCALIZED_GERMAN_NAME, BACKGROUND_ORIGINAL_NAME)
            sprite_dict[sprite_name] = sprite
        for scratch_sprite in scratch_project.objects:
            sprite_name = scratch_sprite.name
            sprite_object = sprite_dict[sprite_name]
            variable_list = scratch_sprite.monitors.keys()
            for variable in variable_list:
                scripts = sprite_object.getScriptList()
                found_show_var = False
                for script in scripts:
                    bricks = script.getBrickList()
                    found_show_var = any(filter(lambda brick: (isinstance(brick, catbricks.ShowTextBrick) \
                                                               or isinstance(brick, catbricks.ShowTextColorSizeAlignmentBrick)) \
                                                              and brick.getUserVariable().getName() == variable, bricks))
                    if found_show_var: break
                assert found_show_var

    # workaround for distanceTo-brick with the mouse-pointer as target
    def test_can_convert_distance_to_brick_with_mouse_pointer_as_target(self):
        catrobat_program = self._test_project("distance_to_mouse_pointer")
        assert catrobat_program is not None
        self._test_mouse_pointer_tracking_workaround(catrobat_program)

    # glideTo-brick workaround with mouse-pointer as target
    def test_can_convert_glide_to_brick_with_mouse_pointer_as_target(self):
        catrobat_program = self._test_project("glide_to_mouse_pointer")
        assert catrobat_program is not None
        self._test_mouse_pointer_tracking_workaround(catrobat_program)

    # full_test_no_var
    def test_can_convert_project_without_variables(self):
        self._test_project("full_test_no_var")

    # keys_pressed
    def test_can_convert_project_with_keys(self):
        for project_name in ("keys_pressed", ):
            self._test_project(project_name)

    def test_can_convert_project_with_mediafiles(self):
        self._test_project("Hannah_Montana")

    # simple test project
    def test_can_convert_project_with_unusued_files(self):
        self._test_project("simple")

    def test_can_rewrite_svg_matrix(self):
        tree = ET.parse("test/res/scratch/Wizard_Spells/3.svg")
        root = tree.getroot()
        for child in root:
            if re.search('.*}g', child.tag) != None:
                if 'transform' in child.attrib:
                    assert(child.attrib['transform'] == "matrix(1.5902323722839355, 0, 0, 1.5902323722839355, -0.5, 0.5)")
        svgtopng._parse_and_rewrite_svg_file("test/res/scratch/Wizard_Spells/3.svg","test/res/scratch/Wizard_Spells/3_changed.svg", ns_registry_lock)
        tree = ET.parse("test/res/scratch/Wizard_Spells/3_changed.svg")
        root = tree.getroot()
        for child in root:
            if re.search('.*}g', child.tag) != None:
                if 'transform' in child.attrib:
                    assert(child.attrib['transform'] == "matrix(1, 0, 0, 1, -0.5, 0.5)")

    def test_can_rewrite_svg_text_position(self):
        tree = ET.parse("test/res/scratch/Wizard_Spells/6.svg")
        root = tree.getroot()
        for child in root:
            if re.search('.*}text', child.tag) != None:
                assert(child.attrib['x'] == '147.5')
                assert(child.attrib['y'] == '146.1')
        svgtopng._parse_and_rewrite_svg_file("test/res/scratch/Wizard_Spells/6.svg","test/res/scratch/Wizard_Spells/6_changed.svg", ns_registry_lock)
        tree = ET.parse("test/res/scratch/Wizard_Spells/6_changed.svg")
        root = tree.getroot()
        for child in root:
            if re.search('.*}text', child.tag) != None:
                assert(child.attrib['x'] == '3')
                assert(child.attrib['y'] == '24')

class TestShowVariablesWorkaround(unittest.TestCase):
    def setUp(self):
        self.scratch_project = scratch.Project(common_testing.get_test_project_path("show_variables"))
        assert self.scratch_project
        self.context = converter.Context()
        self.catrobat_project = converter.converted(self.scratch_project, None, self.context)
        assert self.catrobat_project
        self.default_scene = self.catrobat_project.catrobat_program.getDefaultScene()
        assert self.default_scene
        sprite_list = self.default_scene.getSpriteList()
        self.assertEqual(6, len(sprite_list))
        [self.stage_sprite, self.sprite2, self.sprite1, self.global_slider_sprite, self.toggle_slider_sprite, self.local_slider_sprite] = sprite_list

    def test_sprite1_correct_events_added(self):
        #Sprite1
        self.assertEqual(5, self.sprite1.getNumberOfScripts())
        scriptlist = self.sprite1.getScriptList()
        self.assertIsInstance(self.sprite1.getScript(0), catbase.StartScript)
        self.assertIsInstance(self.sprite1.getScript(1), catbase.BroadcastScript)
        self.assertEqual(("S2CC:slider_" + self.sprite1.getName() + "_" + "local_slider").lower(),
                         self.sprite1.getScript(1).getBroadcastMessage())
        self.assertIsInstance(self.sprite1.getScript(2), catbase.WhenConditionScript)
        self.assertIsInstance(self.sprite1.getScript(3), catbase.BroadcastScript)
        self.assertEqual(converter.get_broadcast_show_msg(self.sprite1.getName(), "local_slider", False),
                         self.sprite1.getScript(3).getBroadcastMessage())
        self.assertIsInstance(self.sprite1.getScript(4), catbase.BroadcastScript)
        self.assertEqual(converter.get_broadcast_show_msg(self.sprite1.getName(), "local_default", False),
                         self.sprite1.getScript(4).getBroadcastMessage())
        #local slider sprite
        assert self.local_slider_sprite.getName().startswith(converter.SLIDER_SPRITE_NAME + self.sprite1.getName())
        self.assertEqual(3, self.local_slider_sprite.getNumberOfScripts())
        self.assertIsInstance(self.local_slider_sprite.getScript(0), catbase.StartScript)
        self.assertIsInstance(self.local_slider_sprite.getScript(1), catbase.WhenScript)
        self.assertIsInstance(self.local_slider_sprite.getScript(2), catbase.BroadcastScript)
        self.assertEqual(converter.get_broadcast_show_msg(self.sprite1.getName(), "local_slider", False),
                         self.local_slider_sprite.getScript(2).getBroadcastMessage())

    def test_sprite2_correct_events_added(self):
        #Sprite2
        self.assertEqual(8, self.sprite2.getNumberOfScripts())
        self.assertIsInstance(self.sprite2.getScript(0), catbase.StartScript)
        self.assertIsInstance(self.sprite2.getScript(1), catbase.WhenScript)
        self.assertIsInstance(self.sprite2.getScript(2), catbase.BroadcastScript)
        self.assertEqual(("S2CC:slider_" + self.sprite2.getName() + "_" + "toggle_slider").lower(),
                         self.sprite2.getScript(2).getBroadcastMessage())
        self.assertIsInstance(self.sprite2.getScript(3), catbase.WhenConditionScript)
        self.assertIsInstance(self.sprite2.getScript(4), catbase.BroadcastScript)
        self.assertEqual(converter.get_broadcast_show_msg(self.sprite2.getName(), "toggle_slider"),
                         self.sprite2.getScript(4).getBroadcastMessage())
        self.assertIsInstance(self.sprite2.getScript(5), catbase.BroadcastScript)
        self.assertEqual(converter.get_broadcast_show_msg(self.sprite2.getName(), "toggle_slider", is_hide=True),
                         self.sprite2.getScript(5).getBroadcastMessage())
        self.assertIsInstance(self.sprite2.getScript(6), catbase.BroadcastScript)
        self.assertEqual(converter.get_broadcast_show_msg(self.sprite2.getName(), "toggle_default"),
                         self.sprite2.getScript(6).getBroadcastMessage())
        self.assertIsInstance(self.sprite2.getScript(7), catbase.BroadcastScript)
        self.assertEqual(converter.get_broadcast_show_msg(self.sprite2.getName(), "toggle_default", is_hide=True),
                         self.sprite2.getScript(7).getBroadcastMessage())
        #toggle slider sprite
        assert self.toggle_slider_sprite.getName().startswith(converter.SLIDER_SPRITE_NAME + self.sprite2.getName())
        self.assertEqual(4, self.toggle_slider_sprite.getNumberOfScripts())
        self.assertIsInstance(self.toggle_slider_sprite.getScript(0), catbase.StartScript)
        self.assertIsInstance(self.toggle_slider_sprite.getScript(1), catbase.WhenScript)
        self.assertIsInstance(self.toggle_slider_sprite.getScript(2), catbase.BroadcastScript)
        self.assertEqual(converter.get_broadcast_show_msg(self.sprite2.getName(), "toggle_slider", False),
                         self.toggle_slider_sprite.getScript(2).getBroadcastMessage())
        self.assertIsInstance(self.toggle_slider_sprite.getScript(3), catbase.BroadcastScript)
        self.assertEqual(converter.get_broadcast_show_msg(self.sprite2.getName(), "toggle_slider", False, True),
                         self.toggle_slider_sprite.getScript(3).getBroadcastMessage())

    def test_stage_correct_events_added(self):
        assert self.global_slider_sprite.getName().startswith(converter.SLIDER_SPRITE_NAME + self.stage_sprite.getName())
        #Stage
        self.assertEqual(3, self.stage_sprite.getNumberOfScripts())
        self.assertIsInstance(self.stage_sprite.getScript(0), catbase.StartScript)
        self.assertIsInstance(self.stage_sprite.getScript(1), catbase.BroadcastScript)
        self.assertEqual(converter.get_broadcast_show_msg(self.stage_sprite.getName(), "s2cc:sensor_stage_soundlevel", True),
                         self.stage_sprite.getScript(1).getBroadcastMessage())
        self.assertIsInstance(self.stage_sprite.getScript(2), catbase.BroadcastScript)
        self.assertEqual(converter.get_broadcast_show_msg(self.stage_sprite.getName(), "global_default", True),
                         self.stage_sprite.getScript(2).getBroadcastMessage())
        #global slider sprite
        self.assertEqual(4, self.global_slider_sprite.getNumberOfScripts())
        self.assertIsInstance(self.global_slider_sprite.getScript(0), catbase.StartScript)
        self.assertIsInstance(self.global_slider_sprite.getScript(1), catbase.WhenConditionScript)
        self.assertIsInstance(self.global_slider_sprite.getScript(2), catbase.WhenScript)
        self.assertIsInstance(self.global_slider_sprite.getScript(3), catbase.BroadcastScript)
        self.assertEqual(converter.get_broadcast_show_msg(self.global_slider_sprite.getName(), "global_slider", True),
                         self.global_slider_sprite.getScript(3).getBroadcastMessage())

    def test_local_sensor_converted(self):
        sprite_start = self.sprite1.scriptList[0]
        [copy_loop] = filter(lambda brick: isinstance(brick, catbricks.ForeverBrick), sprite_start.getBrickList())
        copy_bricks = filter(lambda brick: isinstance(brick, catbricks.SetVariableBrick), copy_loop.loopBricks)
        self.assertEqual(1, len(copy_bricks))
        [copy_brick] = copy_bricks
        self.assertIsInstance(copy_brick, catbricks.SetVariableBrick)
        self.assertEqual("S2CC:sensor_Sprite1_xpos", copy_brick.getUserVariable().getName())

    def test_global_sensor_converted(self):
        stage_start = self.stage_sprite.scriptList[0]
        [copy_loop] = filter(lambda brick: isinstance(brick, catbricks.ForeverBrick), stage_start.getBrickList())
        copy_bricks = filter(lambda brick: isinstance(brick, catbricks.SetVariableBrick), copy_loop.loopBricks)
        self.assertEqual(1, len(copy_bricks))
        [copy_brick] = copy_bricks
        self.assertIsInstance(copy_brick, catbricks.SetVariableBrick)
        self.assertEqual("S2CC:sensor_Stage_soundLevel", copy_brick.getUserVariable().getName())




if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()