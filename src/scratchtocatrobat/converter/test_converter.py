#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2015 The Catrobat Team
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

import org.catrobat.catroid.common as catcommon
import org.catrobat.catroid.content as catbase
from org.catrobat.catroid.ui.fragment import SpriteFactory
import org.catrobat.catroid.content.bricks as catbricks
import org.catrobat.catroid.content.bricks.Brick as catbasebrick
import org.catrobat.catroid.formulaeditor as catformula

from scratchtocatrobat.converter import catrobat
from scratchtocatrobat.tools import common
from scratchtocatrobat.tools import common_testing
from scratchtocatrobat.scratch import scratch
from scratchtocatrobat.converter import converter


def create_catrobat_sprite_stub(name=None):
    sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, "Dummy" if name is None else name)
    looks = sprite.getLookDataList()
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
#         catr_script = converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE)
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
#             assert look.getLookName() == expected_name
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

    test_project = catbase.Project(None, "__test_project__")
    test_scene = catbase.Scene(None, "Scene 1",test_project)
    test_project.sceneList.add(test_scene)
    block_converter = converter._ScratchObjectConverter(test_project, None)
    _name_of_test_list = "my_test_list"

    def setUp(self):
        super(TestConvertBlocks, self).setUp()
        # create and add user list for user list bricks to project
        self.block_converter._catrobat_scene.getDataContainer().addProjectUserList(self._name_of_test_list)
        # create dummy sprite
        self.sprite_stub = create_catrobat_background_sprite_stub()

    def get_sprite_with_soundinfo(self, soundinfo_name):
        dummy_sound = catcommon.SoundInfo()
        dummy_sound.setTitle(soundinfo_name)
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
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE)
        self.assertTrue(isinstance(catr_script, catbase.BroadcastScript))
        self.assertEqual(broadcast_message, catr_script.getBroadcastMessage())

    # whenIReceive
    def test_can_convert_broadcast_script_by_ignoring_case_sensitive_broadcast_message(self):
        broadcast_message = "hElLo WOrLD" # mixed case letters...
        scratch_script = scratch.Script([30, 355, [["whenIReceive", broadcast_message], ["changeGraphicEffect:by:", "color", 25]]])
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE)
        self.assertTrue(isinstance(catr_script, catbase.BroadcastScript))
        self.assertNotEqual(catr_script.getBroadcastMessage(), broadcast_message)
        self.assertEqual(catr_script.getBroadcastMessage(), broadcast_message.lower())

    # whenKeyPressed
    def test_can_convert_keypressed_script(self):
        scratch_script = scratch.Script([30, 355, [["whenKeyPressed", "space"], ["changeGraphicEffect:by:", "color", 25]]])
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE)
        # KeyPressed-scripts are represented with broadcast-scripts with a special key-message
        self.assertTrue(isinstance(catr_script, catbase.BroadcastScript))
        self.assertEqual(converter._key_to_broadcast_message("space"), catr_script.getBroadcastMessage())

    # whenClicked
    def test_can_convert_whenclicked_script(self):
        scratch_script = scratch.Script([30, 355, [["whenClicked"], ["changeGraphicEffect:by:", "color", 25]]])
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE)
        self.assertTrue(isinstance(catr_script, catbase.WhenScript))
        self.assertEqual('Tapped', catr_script.getAction())

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
        exponent, base = 6, 10
        scratch_block = ["10 ^", exponent]
        [rounded_result_formula_element] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(rounded_result_formula_element, catformula.FormulaElement)
        assert rounded_result_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert rounded_result_formula_element.value == catformula.Functions.ROUND.toString() # @UndefinedVariable
        assert rounded_result_formula_element.rightChild == None
        result_formula_element = rounded_result_formula_element.leftChild
        assert result_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert result_formula_element.value == catformula.Functions.EXP.toString() # @UndefinedVariable
        assert result_formula_element.rightChild == None
        mult_formula_element = result_formula_element.leftChild
        assert mult_formula_element.type == catformula.FormulaElement.ElementType.OPERATOR
        assert mult_formula_element.value == catformula.Operators.MULT.toString() # @UndefinedVariable
        value_formula_element = mult_formula_element.leftChild
        assert value_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert value_formula_element.value == str(exponent)
        assert value_formula_element.leftChild == None
        assert value_formula_element.rightChild == None
        ln_formula_element = mult_formula_element.rightChild
        assert ln_formula_element.type == catformula.FormulaElement.ElementType.FUNCTION
        assert ln_formula_element.value == catformula.Functions.LN.toString() # @UndefinedVariable
        assert ln_formula_element.rightChild == None
        base_formula_element = ln_formula_element.leftChild
        assert base_formula_element.type == catformula.FormulaElement.ElementType.NUMBER
        assert base_formula_element.value == str(base)
        assert base_formula_element.leftChild == None
        assert base_formula_element.rightChild == None

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

    ###############################################################################################################
    #
    # Brick block tests
    #
    ###############################################################################################################

    def test_fail_on_unknown_block(self):
        #with self.assertRaises(common.ScratchtobatError):
        [catr_brick] = self.block_converter._catrobat_bricks_from(['wrong_block_name_zzz', 10, 10], DUMMY_CATR_SPRITE)
        # TODO: change to note-brick check later!!!
        #assert isinstance(catr_brick, catbricks.NoteBrick)
        assert isinstance(catr_brick, converter.UnmappedBlock)

    # doIf
    def test_can_convert_if_block(self):
        expected_value_left_operand = "1"
        expected_value_right_operand = "2"
        scratch_do_if = ["doIf", ["=", expected_value_left_operand, expected_value_right_operand],
                         [["wait:elapsed:from:", 1], ["wait:elapsed:from:", 2]]]
        catr_do_if = self.block_converter._catrobat_bricks_from(scratch_do_if, DUMMY_CATR_SPRITE)

        assert isinstance(scratch_do_if, list)
        assert len(catr_do_if) == 4
        expected_brick_classes = [catbricks.IfThenLogicBeginBrick, catbricks.WaitBrick,
                                  catbricks.WaitBrick, catbricks.IfThenLogicEndBrick]
        assert [_.__class__ for _ in catr_do_if] == expected_brick_classes

        if_then_logic_begin_brick = catr_do_if[0]
        if_then_logic_end_brick = catr_do_if[3]

        assert if_then_logic_begin_brick.ifEndBrick == if_then_logic_end_brick
        assert if_then_logic_end_brick.ifBeginBrick == if_then_logic_begin_brick

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
        assert len(catr_do_if) == 5
        expected_brick_classes = [catbricks.IfLogicBeginBrick, catbricks.WaitBrick,
                                  catbricks.IfLogicElseBrick, catbricks.WaitBrick,
                                  catbricks.IfLogicEndBrick]
        assert [_.__class__ for _ in catr_do_if] == expected_brick_classes

        if_logic_begin_brick = catr_do_if[0]
        if_logic_else_brick = catr_do_if[2]
        if_logic_end_brick = catr_do_if[4]

        assert if_logic_begin_brick.getIfElseBrick() == if_logic_else_brick
        assert if_logic_begin_brick.getIfEndBrick() == if_logic_end_brick

        assert if_logic_else_brick.getIfBeginBrick() == if_logic_begin_brick
        assert if_logic_else_brick.getIfEndBrick() == if_logic_end_brick

        assert if_logic_end_brick.getIfBeginBrick() == if_logic_begin_brick
        assert if_logic_end_brick.getIfElseBrick() == if_logic_else_brick

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
        assert len(catr_do_loop) == 8
        expected_brick_classes = [catbricks.RepeatBrick, catbricks.MoveNStepsBrick, catbricks.WaitBrick, catbricks.NoteBrick, catbricks.MoveNStepsBrick, catbricks.WaitBrick, catbricks.NoteBrick, catbricks.LoopEndBrick]
        assert [_.__class__ for _ in catr_do_loop] == expected_brick_classes

    # doUntil
    def test_can_convert_do_until_block(self):
        expected_value_left_operand = "1"
        expected_value_right_operand = "2"
        scratch_block = ["doUntil", ["<", expected_value_left_operand, expected_value_right_operand],
                         [["forward:", 10], ["wait:elapsed:from:", 1]]]
        catr_do_until_loop = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_do_until_loop, list)
        assert len(catr_do_until_loop) == 4
        expected_brick_classes = [catbricks.RepeatUntilBrick, catbricks.MoveNStepsBrick,
                                  catbricks.WaitBrick, catbricks.LoopEndBrick]
        assert [_.__class__ for _ in catr_do_until_loop] == expected_brick_classes

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
    def test_fail_convert_playsound_block_if_sound_missing(self):
        scratch_block = ["playSound:", "bird"]
        bricks = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert len(bricks) == 2
        assert isinstance(bricks[0], catbricks.WaitBrick)
        assert isinstance(bricks[1], catbricks.NoteBrick)

    # playSound:
    def test_can_convert_playsound_block(self):
        scratch_block = _, expected_sound_name = ["playSound:", "bird"]
        dummy_sprite = self.get_sprite_with_soundinfo(expected_sound_name)
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, dummy_sprite)
        assert isinstance(catr_brick, catbricks.PlaySoundBrick)
        assert catr_brick.sound.getTitle() == expected_sound_name

    # doPlaySoundAndWait
    def test_fail_convert_doplaysoundandwait_block(self):
        scratch_block = ["doPlaySoundAndWait", "bird"]
        bricks = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert len(bricks) == 2
        assert isinstance(bricks[0], catbricks.WaitBrick)
        assert isinstance(bricks[1], catbricks.NoteBrick)

    # doPlaySoundAndWait
    def test_can_convert_doplaysoundandwait_block(self):
        scratch_block = _, expected_sound_name = ["doPlaySoundAndWait", "bird"]
        dummy_sprite = self.get_sprite_with_soundinfo(expected_sound_name)
        [play_sound_and_wait_brick] = self.block_converter._catrobat_bricks_from(scratch_block, dummy_sprite)
        assert isinstance(play_sound_and_wait_brick, catbricks.PlaySoundAndWaitBrick)
        assert play_sound_and_wait_brick.sound.getTitle() == expected_sound_name

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

    # showVariableBrick:
    def test_can_convert_show_variable_block(self):
        # create user variable
        variable_name = "test_var"
        project = self.block_converter._catrobat_project
        catrobat.add_user_variable(project, variable_name, DUMMY_CATR_SPRITE, DUMMY_CATR_SPRITE.getName())
        user_variable = project.getDefaultScene().getDataContainer().getUserVariable(variable_name, DUMMY_CATR_SPRITE)
        assert user_variable is not None
        assert user_variable.getName() == variable_name

        # create and validate show variable brick
        scratch_block = ["showVariable:", variable_name]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.ShowVariableBrick)

        #Commented out because members aren't present anymore
        #assert catr_brick.userVariableName == variable_name
        #assert user_variable == catr_brick.userVariable
        #assert catr_brick.userVariable.getName() == variable_name

    # hideVariableBrick:
    def test_can_convert_hide_variable_block(self):
        # create user variable
        variable_name = "test_var"
        project = self.block_converter._catrobat_project
        catrobat.add_user_variable(project, variable_name, DUMMY_CATR_SPRITE, DUMMY_CATR_SPRITE.getName())
        user_variable = project.getDefaultScene().getDataContainer().getUserVariable(variable_name, DUMMY_CATR_SPRITE)
        assert user_variable is not None
        assert user_variable.getName() == variable_name

        # create and validate show variable brick
        scratch_block = ["hideVariable:", variable_name]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.HideVariableBrick)
        
        #Commented out because members aren't present anymore
        #assert catr_brick.userVariableName == variable_name
        #assert user_variable == catr_brick.userVariable
        #assert catr_brick.userVariable.getName() == variable_name
        
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
        assert isinstance(catr_brick, catbricks.InsertItemIntoUserListBrick)

        formula_tree_index = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.INSERT_ITEM_INTO_USERLIST_INDEX).formulaTree # @UndefinedVariable
        assert formula_tree_index.type == catformula.FormulaElement.ElementType.FUNCTION
        assert formula_tree_index.value == "NUMBER_OF_ITEMS"
        assert formula_tree_index.leftChild
        assert formula_tree_index.rightChild == None
        formula_element_left_child = formula_tree_index.leftChild
        assert formula_element_left_child.type == catformula.FormulaElement.ElementType.USER_LIST
        assert formula_element_left_child.value == self._name_of_test_list
        assert formula_element_left_child.leftChild == None
        assert formula_element_left_child.rightChild == None
        formula_tree_value = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.INSERT_ITEM_INTO_USERLIST_VALUE).formulaTree # @UndefinedVariable
        assert formula_tree_value.type == catformula.FormulaElement.ElementType.STRING
        assert formula_tree_value.value == value
        assert formula_tree_value.leftChild == None
        assert formula_tree_value.rightChild == None

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
        assert len(catr_brick_list) == 3
        assert isinstance(catr_brick_list[0], catbricks.RepeatBrick)

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

        formula_tree_list_delete_item = catr_brick_list[1].getFormulaWithBrickField(catbasebrick.BrickField.LIST_DELETE_ITEM).formulaTree # @UndefinedVariable
        assert formula_tree_list_delete_item.type == catformula.FormulaElement.ElementType.NUMBER
        assert formula_tree_list_delete_item.value == "1"
        assert formula_tree_list_delete_item.leftChild == None
        assert formula_tree_list_delete_item.rightChild == None

        assert catr_brick_list[0].loopEndBrick == catr_brick_list[2]
        assert catr_brick_list[2].loopBeginBrick == catr_brick_list[0]

        assert isinstance(catr_brick_list[1], catbricks.DeleteItemOfUserListBrick)
        assert isinstance(catr_brick_list[2], catbricks.LoopEndBrick)

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
        scratch_block = _, look_name = ["startScene", "look1"]
        script = scratch.Script([30, 355, [['whenGreenFlag'], scratch_block]])
        project = catbase.Project(None, "TestDummyProject")
        scene = catbase.Scene(None, "Scene 1", project)
        scene.addSprite(self.sprite_stub)
        project.sceneList.add(scene)
        converter._catr_project = project
        catr_script = self.block_converter._catrobat_script_from(script, self.sprite_stub)
        converter._catr_project = None
        stub_scripts = self.sprite_stub.scriptList
        assert stub_scripts.size() == 1
        assert isinstance(stub_scripts.get(0), catbase.BroadcastScript)

        expected_msg = converter._background_look_to_broadcast_message(look_name)
        assert expected_msg, stub_scripts.get(0).getBroadcastMessage()
        assert isinstance(catr_script.getBrickList().get(0), catbricks.BroadcastBrick)
        assert expected_msg, catr_script.getBrickList().get(0).getBroadcastMessage()

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

    # thinkBubbleBrick
    def test_can_convert_think_bubble_brick(self):
        scratch_block = _, expected_message = ["think:", "2B or !2B..."]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        print type(catr_brick)
        assert isinstance(catr_brick, catbricks.ThinkBubbleBrick)

        formula_tree = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.STRING).formulaTree # @UndefinedVariable
        assert catformula.FormulaElement.ElementType.STRING == formula_tree.type
        assert expected_message == formula_tree.value
        assert formula_tree.leftChild is None
        assert formula_tree.rightChild is None

    # thinkForBubbleBrick
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


class TestConvertProjects(common_testing.ProjectTestCase):

    def _test_project(self, project_name):
        if os.path.splitext(project_name)[1]:
            tempdir = common.TemporaryDirectory()
            scratch_project_dir = tempdir.name
            self.addCleanup(tempdir.cleanup)
            common.extract(common_testing.get_test_project_packed_file(project_name),
                           scratch_project_dir)
        else:
            scratch_project_dir = common_testing.get_test_project_path(project_name)

        scratch_project = scratch.Project(scratch_project_dir, name=project_name,
                                          id_=common_testing.PROJECT_DUMMY_ID)

        context = converter.Context()
        converted_project = converter.converted(scratch_project, None, context)
        catrobat_zip_file_name = converted_project.save_as_catrobat_package_to(self._testresult_folder_path)
        self.assertValidCatrobatProgramPackageAndUnpackIf(catrobat_zip_file_name, project_name,
                                                          unused_scratch_resources=scratch_project.unused_resource_names)
        return converted_project.catrobat_program

    # full_test_no_var
    def test_can_convert_project_without_variables(self):
        self._test_project("full_test_no_var")

#     # FIXME: fails
#     # TODO: fails because of wrong test file? string values "0" instead of numeric 0
#     def test_can_convert_project_with_variables(self):
#         self._test_project("full_test")

    # keys_pressed
    def test_can_convert_project_with_keys(self):
        for project_name in ("keys_pressed", ):
            self._test_project(project_name)
            

    def test_can_convert_project_with_mediafiles(self):
        scratch_project_to_sound_to_sound_length_map = {
            "Hannah_Montana": {
                ("HandClap", catrobat._BACKGROUND_SPRITE_NAME): 0.0,
                ("rada rada", catrobat._BACKGROUND_SPRITE_NAME): 1.0,
                ("See You Again", "Sprite3"): 4 * 60.0 + 15,
            }
        }
        for project_name, sound_to_sound_length_map in scratch_project_to_sound_to_sound_length_map.iteritems():
            catrobat_project = self._test_project(project_name)
#             for [sound_name, containing_sprite_name], expected_sound_length in sound_to_sound_length_map.iteritems():
            for [sound_name, containing_sprite_name], _ in sound_to_sound_length_map.iteritems():
                sound_length_variable_name = converter._sound_length_variable_name_for(sound_name)
                sound_length_variable = catrobat.user_variable_of(catrobat_project, sound_length_variable_name, containing_sprite_name)
                assert isinstance(sound_length_variable, catformula.UserVariable)
                # TODO: check first set brick for variable
#                 assert sound_length_variable.getValue() == expected_sound_length

    # simple test project
    def test_can_convert_project_with_unusued_files(self):
        self._test_project("simple")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
