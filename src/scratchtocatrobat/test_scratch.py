#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2014 The Catrobat Team
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
import os
import unittest

from scratchtocatrobat import common
from scratchtocatrobat import common_testing
from scratchtocatrobat import scratch

EASY_SCRIPTS = [
    [23, 125,
        [["whenGreenFlag"],
            ["say:duration:elapsed:from:", "Watch me dance!", 2],
            ["doRepeat",
                10,
                [["forward:", 10],
                    ["playDrum", 1, 0.2],
                    ["forward:", -10],
                    ["playDrum", 1, 0.2]]]]],
    [30, 355, [["whenKeyPressed", "space"], ["changeGraphicEffect:by:", "color", 25]]]
]

TEST_PROJECT_FOLDER = "dancing_castle"


class ProjectExtractionTest(common_testing.BaseTestCase):
    def test_can_extract_project(self):
        for project_file in common_testing.TEST_PROJECT_FILENAME_TO_ID_MAP:
            scratch.extract_project(common.get_test_project_packed_file(project_file), self.temp_dir)
            self.assertTrue(scratch.Project(self.temp_dir))


class TestProjectInit(unittest.TestCase):
    def test_can_construct_on_correct_input(self):
        project = scratch.Project(common.get_test_project_path("simple"), name="dummy", id_=common_testing.PROJECT_DUMMY_ID)
        self.assertTrue(project, "No project object")

    def test_fail_on_non_existing_input_path(self):
        with self.assertRaises(EnvironmentError):
            # TODO: check error message
            scratch.Project(common.get_test_project_path("non_existing_path"))

    def test_fail_on_project_with_missing_image_and_sound_files(self):
        with self.assertRaises(scratch.ProjectError):
            # TODO: check error type
            scratch.Project(common.get_test_project_path("missing_resources"))

    def test_fail_on_project_with_missing_sound_files(self):
        with self.assertRaises(scratch.ProjectError):
            # TODO: check error type
            scratch.Project(common.get_test_project_path("missing_image_resources"))


class TestProjectFunc(unittest.TestCase):
    def __init__(self, methodName='runTest',):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.project_folder = TEST_PROJECT_FOLDER

    def setUp(self):
        self.project = scratch.Project(common.get_test_project_path(self.project_folder))

    def test_can_access_project_id(self):
        test_project_folder_to_project_id = {
            "dancing_castle": "10205819",
        }
        for project_folder, project_id in test_project_folder_to_project_id.iteritems():
            project_path = common.get_test_project_path(project_folder)
            self.assertEqual(project_id, scratch.Project(project_path).project_id)

    def test_can_access_md5_name_of_stage_costumes(self):
        expected_stage_customes_md5_names = set(["510da64cf172d53750dffd23fbf73563.png", "033f926829a446a28970f59302b0572d.png"])
        self.assertEqual(expected_stage_customes_md5_names, set(self.project.background_md5_names))

    def test_can_access_listened_pressed_keys(self):
        project = scratch.Project(common.get_test_project_path("keys_pressed"))
        self.assertEqual(set(["d", "c", "a", "4", "8"]), project.listened_keys)

    def test_can_access_unused_resources_of_project(self):
        project = scratch.Project(common.get_test_project_path("simple"), name="simple", id_=common_testing.PROJECT_DUMMY_ID)
        self.assertGreater(len(project.unused_resource_paths), 0)
        self.assertSetEqual(set(['0.png', '2.wav', '3.png', '4.png', '5.png', '6.png', '8.png']), set(map(os.path.basename, project.unused_resource_paths)))

    def test_can_access_sound_and_costume_by_resource_name(self):
        scratch_to_catrobat_resource_names_map = {
            "83a9787d4cb6f3b7632b4ddfebf74367.wav": "83a9787d4cb6f3b7632b4ddfebf74367_pop.wav",
            "510da64cf172d53750dffd23fbf73563.png": "510da64cf172d53750dffd23fbf73563_backdrop1.png",
            "033f926829a446a28970f59302b0572d.png": "033f926829a446a28970f59302b0572d_castle1.png",
            "83c36d806dc92327b9e7049a565c6bff.wav": "83c36d806dc92327b9e7049a565c6bff_meow.wav"}
        for resource_name in scratch_to_catrobat_resource_names_map:
            for data_dict in self.project.find_all_resource_dicts_for(resource_name):
                self.assertTrue("soundName" in data_dict or "costumeName" in data_dict, "No sound or costume data dict")


class TestRawProjectInit(unittest.TestCase):

    def test_can_create_on_correct_file(self):
        self.assertTrue(scratch.RawProject(common.get_test_project_path("dancing_castle")))
        self.assertTrue(scratch.RawProject(common.get_test_project_path("simple")))

    def test_fail_on_corrupt_file(self):
        with self.assertRaises(scratch.UnsupportedProjectFileError):
            scratch.RawProject(common.get_test_project_path("faulty_json_file"))


class TestRawProjectFunc(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.project = scratch.RawProject(common.get_test_project_path("dancing_castle"))

    def test_can_access_scratch_objects(self):
        for scratch_object in self.project.objects:
            self.assertTrue(scratch_object)
            self.assertTrue(isinstance(scratch_object, scratch.Object))
        self.assertEqual("Stage", self.project.objects[0].get_objName(), "Stage object missing")
        self.assertEqual(['Stage', 'Sprite1', 'Cassy Dance'], [_.get_objName() for _ in self.project.objects])

    def test_can_access_stage_object(self):
        stage_object = self.project.stage_object
        self.assertEqual("Stage", stage_object.get_objName())


class TestObjectInit(unittest.TestCase):

    def setUp(self):
        self.project = scratch.Project(common.get_test_project_path(TEST_PROJECT_FOLDER))

    def test_can_construct_on_correct_input(self):
        for raw_object in self.project.raw_objects:
            self.assertTrue(scratch.Object.is_valid_class_input(raw_object))
            self.assertTrue(scratch.Object(raw_object))

    def test_fail_on_wrong_input(self):
        faulty_object_structures = [{},
            ]
        for faulty_input in faulty_object_structures:
            self.assertFalse(scratch.Object.is_valid_class_input(faulty_input), "Wrong input not detected: {}".format(faulty_input))
            with self.assertRaises(scratch.ObjectError):
                scratch.Object(faulty_input)


class TestObjectFunc(unittest.TestCase):

    def setUp(self):
        self.project = scratch.Project(common.get_test_project_path(TEST_PROJECT_FOLDER))
        self.scratch_objects = self.project.objects

    def test_can_access_scratch_scripts(self):
        for scratch_object in self.scratch_objects:
            if scratch_object.get_objName() != "Stage":
                self.assertTrue(len(scratch_object.scripts) > 0)
            for scratch_script in scratch_object.scripts:
                self.assertTrue(scratch_script)
                self.assertTrue(isinstance(scratch_script, scratch.Script))

    def test_can_access_scratch_costumes(self):
        for scratch_object in self.scratch_objects:
            self.assertTrue(len(scratch_object.get_costumes()) > 0)
            for costume in scratch_object.get_costumes():
                self.assertTrue(costume)
                self.assertTrue(isinstance(costume, dict))
                self.assertTrue("costumeName" in costume)

    def test_can_access_scratch_sounds(self):
        for scratch_object in self.scratch_objects:
            self.assertTrue(len(scratch_object.get_sounds()) > 0)
            for sound in scratch_object.get_sounds():
                self.assertTrue(sound)
                self.assertTrue(isinstance(sound, dict))
                self.assertTrue("soundName" in sound)

    def test_can_check_for_stage_object(self):
        for idx, scratch_object in enumerate(self.scratch_objects):
            if idx == 0:
                self.assert_(scratch_object.is_stage_object)
            else:
                self.assert_(not scratch_object.is_stage_object)


class TestScriptInit(unittest.TestCase):

    def test_can_construct_on_correct_input(self):
        for script_input in EASY_SCRIPTS:
            script = scratch.Script(script_input)
            self.assertTrue(script)

    def test_fail_on_wrong_input(self):
        faulty_script_structures = [
            [],
            "a string is no correct input",
            ["the first 2 params", "must be integers", []],
            [0101, 444, "further the third one must be a list"]
        ]
        for faulty_input in faulty_script_structures:
            self.assertFalse(scratch.Script.is_valid_script_input(faulty_input), "Wrong input not detected: {}".format(faulty_input))
            with self.assertRaises(scratch.ScriptError):
                scratch.Script(faulty_input)


class TestScriptFunc(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.script = scratch.Script(EASY_SCRIPTS[0])

    def test_can_access_scratch_script_data(self):
        self.assertEqual('whenGreenFlag', self.script.get_type())
        expected_brick_names = ['say:duration:elapsed:from:', 'doRepeat', 'forward:', 'playDrum', 'forward:', 'playDrum']
        self.assertEqual(expected_brick_names, self.script.get_raw_bricks())


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
