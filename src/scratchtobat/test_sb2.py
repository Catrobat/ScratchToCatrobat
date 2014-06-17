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

from scratchtobat import common
from scratchtobat import sb2

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


class TestProjectInit(unittest.TestCase):
    def test_can_construct_on_correct_input(self):
        project = sb2.Project(common.get_test_project_path("simple"), name="dummy")
        self.assertTrue(project, "No project object")

    def test_fail_on_non_existing_input_path(self):
        with self.assertRaises(EnvironmentError):
            # TODO: check error message
            sb2.Project(common.get_test_project_path("non_existing_path"))

    def test_fail_on_corrupt_sb2_json_input(self):
        with self.assertRaises(sb2.ProjectError):
            # TODO: check error type
            sb2.Project(common.get_test_project_path("faulty_json_file"))

    def test_fail_on_project_with_missing_image_and_sound_files(self):
        with self.assertRaises(sb2.ProjectError):
            # TODO: check error type
            sb2.Project(common.get_test_project_path("missing_resources"))

    def test_fail_on_project_with_missing_sound_files(self):
        with self.assertRaises(sb2.ProjectError):
            # TODO: check error type
            sb2.Project(common.get_test_project_path("missing_image_resources"))


class TestProjectFunc(unittest.TestCase):
    def __init__(self, methodName='runTest',):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.project_folder = TEST_PROJECT_FOLDER

    def setUp(self):
        self.project = sb2.Project(common.get_test_project_path(self.project_folder))

    def test_can_access_project_name(self):
        test_project_folder_to_project_name = {
            "dancing_castle": "10205819",
        }
        for project_folder, project_name in test_project_folder_to_project_name.iteritems():
            project_path = common.get_test_project_path(project_folder)
            self.assertEqual(project_name, sb2.Project(project_path).name)

    def test_can_access_md5_name_of_stage_costumes(self):
        expected_stage_customes_md5_names = set(["510da64cf172d53750dffd23fbf73563.png", "033f926829a446a28970f59302b0572d.png"])
        self.assertEqual(expected_stage_customes_md5_names, set(self.project.background_md5_names))

    def test_can_access_listened_pressed_keys(self):
        project = sb2.Project(common.get_test_project_path("keys_pressed"))
        self.assertEqual(set(["d", "c", "a", "4", "8"]), project.listened_keys)

    def test_can_access_unused_resources_of_project(self):
        project = sb2.Project(common.get_test_project_path("simple"), name="simple")
        self.assertGreater(len(project.unused_resource_paths), 0)
        self.assertSetEqual(set(['0.png', '2.wav', '3.png', '4.png', '5.png', '6.png', '8.png']), set(map(os.path.basename, project.unused_resource_paths)))


class TestProjectCodeInit(unittest.TestCase):

    def test_can_create_on_correct_file(self):
        self.assertTrue(sb2.ProjectCode(common.get_test_project_path("dancing_castle")))
        self.assertTrue(sb2.ProjectCode(common.get_test_project_path("simple")))

    def test_fail_on_corrupt_file(self):
        with self.assertRaises(sb2.ProjectCodeError):
            sb2.ProjectCode(common.get_test_project_path("faulty_json_file"))


class TestProjectCodeFunc(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.project_code = sb2.ProjectCode(common.get_test_project_path("dancing_castle"))

    def test_can_access_sb2_objects(self):
        for sb2_object in self.project_code.objects:
            self.assertTrue(sb2_object)
            self.assertTrue(isinstance(sb2_object, sb2.Object))
        self.assertEqual("Stage", self.project_code.objects[0].get_objName(), "Stage object missing")
        self.assertEqual(['Stage', 'Sprite1', 'Cassy Dance'], [_.get_objName() for _ in self.project_code.objects])

    def test_can_access_sound_and_costume_by_resource_name(self):
        sb2_to_catrobat_resource_names_map = {
            "83a9787d4cb6f3b7632b4ddfebf74367.wav": "83a9787d4cb6f3b7632b4ddfebf74367_pop.wav",
            "510da64cf172d53750dffd23fbf73563.png": "510da64cf172d53750dffd23fbf73563_backdrop1.png",
            "033f926829a446a28970f59302b0572d.png": "033f926829a446a28970f59302b0572d_castle1.png",
            "83c36d806dc92327b9e7049a565c6bff.wav": "83c36d806dc92327b9e7049a565c6bff_meow.wav"}
        for resource_name in sb2_to_catrobat_resource_names_map:
            for data_dict in self.project_code.find_all_resource_dicts_for(resource_name):
                self.assertTrue("soundName" in data_dict or "costumeName" in data_dict, "No sound or costume data dict")

    def test_can_access_stage_object(self):
        stage_object = self.project_code.stage_object
        self.assertEqual("Stage", stage_object.get_objName())


class TestObjectInit(unittest.TestCase):

    def setUp(self):
        self.project = sb2.Project(common.get_test_project_path(TEST_PROJECT_FOLDER))

    def test_can_construct_on_correct_input(self):
        for obj_data in self.project.project_code.objects_data:
            self.assertTrue(sb2.Object.is_valid_class_input(obj_data))
            self.assertTrue(sb2.Object(obj_data))

    def test_fail_on_wrong_input(self):
        faulty_object_structures = [{},
            ]
        for faulty_input in faulty_object_structures:
            self.assertFalse(sb2.Object.is_valid_class_input(faulty_input), "Wrong input not detected: {}".format(faulty_input))
            with self.assertRaises(sb2.ObjectError):
                sb2.Object(faulty_input)


class TestObjectFunc(unittest.TestCase):

    def setUp(self):
        self.project = sb2.Project(common.get_test_project_path(TEST_PROJECT_FOLDER))
        self.sb2_objects = self.project.project_code.objects

    def test_can_access_sb2_scripts(self):
        for sb2_object in self.sb2_objects:
            if sb2_object.get_objName() != "Stage":
                self.assertTrue(len(sb2_object.scripts) > 0)
            for sb2_script in sb2_object.scripts:
                self.assertTrue(sb2_script)
                self.assertTrue(isinstance(sb2_script, sb2.Script))

    def test_can_access_sb2_costumes(self):
        for sb2_object in self.sb2_objects:
            self.assertTrue(len(sb2_object.get_costumes()) > 0)
            for costume in sb2_object.get_costumes():
                self.assertTrue(costume)
                self.assertTrue(isinstance(costume, dict))
                self.assertTrue("costumeName" in costume)

    def test_can_access_sb2_sounds(self):
        for sb2_object in self.sb2_objects:
            self.assertTrue(len(sb2_object.get_sounds()) > 0)
            for sound in sb2_object.get_sounds():
                self.assertTrue(sound)
                self.assertTrue(isinstance(sound, dict))
                self.assertTrue("soundName" in sound)

    def test_can_check_for_stage_object(self):
        for idx, sb2_object in enumerate(self.sb2_objects):
            if idx == 0:
                self.assert_(sb2_object.is_stage_object)
            else:
                self.assert_(not sb2_object.is_stage_object)


class TestScriptInit(unittest.TestCase):

    def test_can_construct_on_correct_input(self):
        for script_input in EASY_SCRIPTS:
            script = sb2.Script(script_input)
            self.assertTrue(script)

    def test_fail_on_wrong_input(self):
        faulty_script_structures = [
            [],
            "a string is no correct input",
            ["the first 2 params", "must be integers", []],
            [0101, 444, "further the third one must be a list"]
        ]
        for faulty_input in faulty_script_structures:
            self.assertFalse(sb2.Script.is_valid_script_input(faulty_input), "Wrong input not detected: {}".format(faulty_input))
            with self.assertRaises(sb2.ScriptError):
                sb2.Script(faulty_input)


class TestScriptFunc(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.script = sb2.Script(EASY_SCRIPTS[0])

    def test_can_access_sb2_script_data(self):
        self.assertEqual('whenGreenFlag', self.script.get_type())
        expected_brick_names = ['say:duration:elapsed:from:', 'doRepeat', 'forward:', 'playDrum', 'forward:', 'playDrum']
        self.assertEqual(expected_brick_names, self.script.get_raw_bricks())


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
