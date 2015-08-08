#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2015 The Catrobat Team
#  (<http://developer.catrobat.org/credits>)
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
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
import glob
import os
import unittest

import org.catrobat.catroid.common as catcommon
import org.catrobat.catroid.content as catbase
import org.catrobat.catroid.content.bricks as catbricks
import org.catrobat.catroid.content.bricks.Brick as catbasebrick
import org.catrobat.catroid.formulaeditor as catformula

from scratchtocatrobat import catrobat
from scratchtocatrobat import common
from scratchtocatrobat import common_testing
from scratchtocatrobat import scratch
from scratchtocatrobat import converter


def create_catrobat_sprite_stub(name=None):
    sprite = catbase.Sprite("Dummy" if name is None else name)
    looks = sprite.getLookDataList()
    for lookname in ["look1", "look2", "look3"]:
        looks.add(catrobat.create_lookdata(lookname, None))
    return sprite

def create_catrobat_background_sprite_stub():
    return create_catrobat_sprite_stub(catrobat._BACKGROUND_SPRITE_NAME)

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


def ConverterTestClass(class_):
    class Wrapper:
        def __init__(self, *args, **kwargs):
            _dummy_project = catbase.Project(None, "__test_project__")
            self.block_converter = converter._ScratchObjectConverter(_dummy_project)
            class_(*args, **kwargs)
    return Wrapper


#@ConverterTestClass
class TestConvertBlocks(common_testing.BaseTestCase):
    block_converter = converter._ScratchObjectConverter(catbase.Project(None, "__test_project__"))

    def setUp(self):
        super(TestConvertBlocks, self).setUp()
        self.sprite_stub = create_catrobat_background_sprite_stub()

    def get_sprite_with_soundinfo(self, soundinfo_name):
        dummy_sound = catcommon.SoundInfo()
        dummy_sound.setTitle(soundinfo_name)
        dummy_sprite = catbase.Sprite("TestDummy")
        dummy_sprite.getSoundList().add(dummy_sound)
        return dummy_sprite

    def test_fail_on_unknown_block(self):
        #with self.assertRaises(common.ScratchtobatError):
        [catr_brick] = self.block_converter._catrobat_bricks_from(['wrong_block_name_zzz', 10, 10], DUMMY_CATR_SPRITE)
        # TODO: change to note-brick check later!!!
        #assert isinstance(catr_brick, catbricks.NoteBrick)
        assert isinstance(catr_brick, converter.UnmappedBlock)

    def test_can_convert_loop_blocks(self):
        scratch_do_loop = ["doRepeat", 10, [[u'forward:', 10], [u'playDrum', 1, 0.2], [u'forward:', -10], [u'playDrum', 1, 0.2]]]
        catr_do_loop = self.block_converter._catrobat_bricks_from(scratch_do_loop, DUMMY_CATR_SPRITE)
        assert isinstance(catr_do_loop, list)
        # 1 loop start + 4 inner loop bricks +2 inner note bricks (playDrum not supported) + 1 loop end = 8
        assert len(catr_do_loop) == 8
        expected_brick_classes = [catbricks.RepeatBrick, catbricks.MoveNStepsBrick, catbricks.WaitBrick, catbricks.NoteBrick, catbricks.MoveNStepsBrick, catbricks.WaitBrick, catbricks.NoteBrick, catbricks.LoopEndBrick]
        assert [_.__class__ for _ in catr_do_loop] == expected_brick_classes

    def test_can_convert_waitelapsedfrom_block(self):
        scratch_block = ["wait:elapsed:from:", 1]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.WaitBrick)
        # TODO: this is no real error and should therefore be suppressed in PyDev...
        formula_tree_seconds = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.TIME_TO_WAIT_IN_SECONDS).formulaTree
        assert formula_tree_seconds.type == catformula.FormulaElement.ElementType.NUMBER  # @UndefinedVariable
        assert formula_tree_seconds.value == "1.0"

    def test_fail_convert_playsound_block_if_sound_missing(self):
        scratch_block = ["playSound:", "bird"]
        with self.assertRaises(converter.ConversionError):
            self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)

    def test_can_convert_playsound_block(self):
        scratch_block = _, sound_name = ["playSound:", "bird"]
        dummy_sprite = self.get_sprite_with_soundinfo(sound_name)
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, dummy_sprite)
        assert isinstance(catr_brick, catbricks.PlaySoundBrick)
        assert catr_brick.sound.getTitle() == sound_name

    def test_can_convert_append_int_to_list_block(self):
        # TODO: create list first...
        scratch_block = ["append:toList:", 1, "my_test_list"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.AddItemToUserListBrick)

    def test_can_convert_append_str_to_list_block(self):
        # TODO: create list first...
        scratch_block = ["append:toList:", "DummyString", "my_test_list"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.AddItemToUserListBrick)

    def test_can_convert_insert_at_numeric_index_in_list_block(self):
        # TODO: create list first...
        scratch_block = ["insert:at:ofList:", "DummyString", 2, "my_test_list"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.InsertItemIntoUserListBrick)

    def test_can_convert_insert_at_last_position_in_list_block(self):
        # TODO: create list first...
        scratch_block = ["insert:at:ofList:", "DummyString", "last", "my_test_list"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.InsertItemIntoUserListBrick)

    def test_can_convert_insert_at_random_position_in_list_block(self):
        # TODO: create list first...
        scratch_block = ["insert:at:ofList:", "DummyString", "random", "my_test_list"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.InsertItemIntoUserListBrick)

    def test_can_convert_delete_line_from_list_by_index_block(self):
        # TODO: create list first...
        scratch_block = ["deleteLine:ofList:", 2, "my_test_list"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.DeleteItemOfUserListBrick)

    def test_can_convert_delete_last_line_from_list_block(self):
        # TODO: create list first...
        scratch_block = ["deleteLine:ofList:", "last", "my_test_list"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.DeleteItemOfUserListBrick)

    def test_can_convert_delete_all_lines_from_list_block(self):
        # TODO: create list first...
        scratch_block = ["deleteLine:ofList:", "all", "my_test_list"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.DeleteItemOfUserListBrick)

    def test_can_convert_doplaysoundandwait_block(self):
        scratch_block = _, sound_name = ["doPlaySoundAndWait", "bird"]
        dummy_sprite = self.get_sprite_with_soundinfo(sound_name)
        [play_sound_brick, wait_brick] = self.block_converter._catrobat_bricks_from(scratch_block, dummy_sprite)
        assert isinstance(play_sound_brick, catbricks.PlaySoundBrick)
        assert play_sound_brick.sound.getTitle() == sound_name
        assert isinstance(wait_brick, catbricks.WaitBrick)
        # FIXME: assert for wait variable is missing

    def test_can_convert_nextcostume_block(self):
        scratch_block = ["nextCostume"]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.NextLookBrick)

    def test_can_convert_glideto_block(self):
        scratch_block = _, glide_duration, glide_x, glide_y = ["glideSecs:toX:y:elapsed:from:", 5, 174, -122]
        [catr_brick] = self.block_converter._catrobat_bricks_from(scratch_block, DUMMY_CATR_SPRITE)
        assert isinstance(catr_brick, catbricks.GlideToBrick)
        # TODO: those errors are no real errors and should therefore be suppressed in PyDev...
        durationInSecondsFormula = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.DURATION_IN_SECONDS)
        xDestinationFormula = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.X_DESTINATION)
        yDestinationFormula = catr_brick.getFormulaWithBrickField(catbasebrick.BrickField.Y_DESTINATION)
        assert int(float(durationInSecondsFormula.formulaTree.getValue())) == glide_duration
        assert int(float(xDestinationFormula.formulaTree.getValue())) == glide_x
        assert -1 * int(float(yDestinationFormula.formulaTree.rightChild.getValue())) == glide_y

    def test_can_convert_startscene_block(self):
        scratch_block = _, look_name = ["startScene", "look1"]
        script = scratch.Script([30, 355, [['whenGreenFlag'], scratch_block]])
        project = catbase.Project(None, "TestDummyProject")
        project.addSprite(self.sprite_stub)
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


@ConverterTestClass
class TestConvertScripts(unittest.TestCase):

    def test_can_convert_broadcast_script(self):
        scratch_script = scratch.Script([30, 355, [["whenIReceive", "space"], ["changeGraphicEffect:by:", "color", 25]]])
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE)
        self.assertTrue(isinstance(catr_script, catbase.BroadcastScript))
        self.assertEqual("space", catr_script.getBroadcastMessage())

    def test_can_convert_keypressed_script(self):
        scratch_script = scratch.Script([30, 355, [["whenKeyPressed", "space"], ["changeGraphicEffect:by:", "color", 25]]])
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE)
        # KeyPressed-scripts are represented with broadcast-scripts with a special key-message
        self.assertTrue(isinstance(catr_script, catbase.BroadcastScript))
        self.assertEqual(converter._key_to_broadcast_message("space"), catr_script.getBroadcastMessage())

    def test_can_convert_whenclicked_script(self):
        scratch_script = scratch.Script([30, 355, [["whenClicked"], ["changeGraphicEffect:by:", "color", 25]]])
        catr_script = self.block_converter._catrobat_script_from(scratch_script, DUMMY_CATR_SPRITE)
        self.assertTrue(isinstance(catr_script, catbase.WhenScript))
        self.assertEqual('Tapped', catr_script.getAction())


class TestConvertProjects(common_testing.ProjectTestCase):

    def _test_project(self, project_name):
        if os.path.splitext(project_name)[1]:
            tempdir = common.TemporaryDirectory()
            scratch_project_dir = tempdir.name
            self.addCleanup(tempdir.cleanup)
            common.extract(common_testing.get_test_project_packed_file(project_name), scratch_project_dir)
        else:
            scratch_project_dir = common_testing.get_test_project_path(project_name)
        scratch_project = scratch.Project(scratch_project_dir, name=project_name, id_=common_testing.PROJECT_DUMMY_ID)
        converted_project = converter.converted(scratch_project)
        catrobat_zip_file_name = converted_project.save_as_catrobat_package_to(self._testresult_folder_path)
        self.assertValidCatrobatProgramPackageAndUnpackIf(catrobat_zip_file_name, project_name, unused_scratch_resources=scratch_project.unused_resource_names)
        return converted_project.catrobat_program

    def test_can_convert_project_without_variables(self):
        self._test_project("full_test_no_var")

#     # FIXME: fails
#     # TODO: fails because of wrong test file? string values "0" instead of numeric 0
#     def test_can_convert_project_with_variables(self):
#         self._test_project("full_test")

    def test_can_convert_project_with_keys(self):
        for project_name in ["keys_pressed", ]:
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
            for [sound_name, containing_sprite_name], expected_sound_length in sound_to_sound_length_map.iteritems():
                sound_length_variable_name = converter._sound_length_variable_name_for(sound_name)
                sound_length_variable = catrobat.user_variable_of(catrobat_project, sound_length_variable_name, containing_sprite_name)
                assert isinstance(sound_length_variable, catformula.UserVariable)
                # TODO: check first set brick for variable
                # assert sound_length_variable.getValue() == expected_sound_length

    def test_can_convert_project_with_unusued_files(self):
        self._test_project("simple")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
