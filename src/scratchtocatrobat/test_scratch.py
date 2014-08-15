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
import json
import os
import string
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
                    ["playDrum", 1, 0.2]]],
            ["changeGraphicEffect:by:", "color", 25],
            ["say:", "test"], ], ],
    [30, 355, [["whenKeyPressed", "space"], ["changeGraphicEffect:by:", "color", 25]]],
    [30.5, 355.5, [["whenKeyPressed", "space"], ["changeGraphicEffect:by:", "color", 25]]],
]

TEST_PROJECT_FOLDER = "dancing_castle"


class ProjectExtractionTest(common_testing.BaseTestCase):
    def test_can_extract_project(self):
        for project_file in common_testing.TEST_PROJECT_FILENAME_TO_ID_MAP:
            common.extract(common_testing.get_test_project_packed_file(project_file), self.temp_dir)
            assert scratch.Project(self.temp_dir)


class TestProjectInit(unittest.TestCase):
    def test_can_construct_on_correct_input(self):
        assert scratch.Project(common_testing.get_test_project_path("simple"), name="dummy", id_=common_testing.PROJECT_DUMMY_ID)

    def test_fail_on_non_existing_input_path(self):
        with self.assertRaises(EnvironmentError):
            # TODO: check error message
            scratch.Project(common_testing.get_test_project_path("non_existing_path"))

    def test_fail_on_project_with_missing_image_and_sound_files(self):
        with self.assertRaises(scratch.ProjectError):
            # TODO: check error type
            scratch.Project(common_testing.get_test_project_path("missing_resources"))

    def test_fail_on_project_with_missing_sound_files(self):
        with self.assertRaises(scratch.ProjectError):
            # TODO: check error type
            scratch.Project(common_testing.get_test_project_path("missing_image_resources"))


class TestProjectFunc(unittest.TestCase):
    def __init__(self, methodName='runTest',):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.project_folder = TEST_PROJECT_FOLDER

    def setUp(self):
        self.project = scratch.Project(common_testing.get_test_project_path(self.project_folder))

    def test_can_access_project_id(self):
        test_project_folder_to_project_id = {
            "dancing_castle": "10205819",
        }
        for project_folder, project_id in test_project_folder_to_project_id.iteritems():
            project_path = common_testing.get_test_project_path(project_folder)
            assert project_id, scratch.Project(project_path).project_id

    def test_can_access_md5_name_of_stage_costumes(self):
        expected_stage_customes_md5_names = set(["510da64cf172d53750dffd23fbf73563.png", "033f926829a446a28970f59302b0572d.png"])
        assert set(self.project.background_md5_names) == expected_stage_customes_md5_names

    def test_can_access_listened_pressed_keys(self):
        project = scratch.Project(common_testing.get_test_project_path("keys_pressed"))
        assert project.listened_keys == set(["d", "c", "a", "4", "8"])

    def test_can_access_unused_resources_of_project(self):
        project = scratch.Project(common_testing.get_test_project_path("simple"), name="simple", id_=common_testing.PROJECT_DUMMY_ID)
        assert len(project.unused_resource_paths) > 0
        assert set(map(os.path.basename, project.unused_resource_paths)) == set(['0.png', '2.wav', '3.png', '4.png', '5.png', '6.png', '8.png'])

    def test_can_access_sound_and_costume_by_resource_name(self):
        scratch_resource_names = {
            "83a9787d4cb6f3b7632b4ddfebf74367.wav",
            "510da64cf172d53750dffd23fbf73563.png",
            "033f926829a446a28970f59302b0572d.png",
            "83c36d806dc92327b9e7049a565c6bff.wav"
        }
        for resource_name in scratch_resource_names:
            for data_dict in self.project.find_all_resource_dicts_for(resource_name):
                assert "soundName" in data_dict or "costumeName" in data_dict


_OBJECT_JSON_STR = '''{
    "objName": "Sprite1",
    $keys
    "currentCostumeIndex": 0,
    "scratchX": 45,
    "scratchY": -102,
    "scale": 1,
    "direction": 90,
    "rotationStyle": "normal"
}'''
_SCRIPT_JSON_STR = '[30, 355, [["whenKeyPressed", "space"], ["dummy_block"]]]'
_SOUND_JSON_STR = '''{
    "soundName": "meow",
    "soundID": 0,
    "md5": "83c36d806dc92327b9e7049a565c6bff.wav",
    "sampleCount": 18688,
    "rate": 22050,
    "format": ""
}'''
_COSTUME_JSON_STR = '''{
    "costumeName": "backdrop1",
    "baseLayerID": 7,
    "baseLayerMD5": "510da64cf172d53750dffd23fbf73563.png",
    "bitmapResolution": 1,
    "rotationCenterX": 240,
    "rotationCenterY": 180
}'''
_VARIABLE_JSON_STR = '''{
    "name": "variable",
    "value": 0,
    "isPersistent": false
}'''


def _object_json_str(**kwargs):
    keys = []
    for key, values in kwargs.iteritems():
        if len(values) > 0:
            keys += ["\"%s\": [%s]" % (key, ",".join(values))]
    # to add trailing comma
    if len(keys) > 0:
        keys += [""]
    return string.Template(_OBJECT_JSON_STR).safe_substitute(keys=",\n".join(keys))


def _default_object_json_str(number_of_scripts=2, number_of_sounds=2, number_of_costumes=2, number_of_variables=2):
    return _object_json_str(scripts=[_SCRIPT_JSON_STR] * number_of_scripts, sounds=[_SOUND_JSON_STR] * number_of_sounds, costumes=[_COSTUME_JSON_STR] * number_of_costumes, variables=[_VARIABLE_JSON_STR] * number_of_variables)


class TestRawProjectInit(unittest.TestCase):
    TEST_PROJECTS = ["dancing_castle", 'simple']

    def test_can_create_from_raw_content(self):
        for project_name in self.TEST_PROJECTS:
            project_data_path = os.path.join(common_testing.get_test_project_path(project_name), scratch._PROJECT_FILE_NAME)
            assert scratch.RawProject.from_project_code_content(common.content_of(project_data_path))

    def test_can_create_from_project_directory(self):
        for project_name in self.TEST_PROJECTS:
            assert scratch.RawProject.from_project_folder_path(common_testing.get_test_project_path(project_name))

    def test_fail_on_corrupt_file(self):
        with self.assertRaises(scratch.UnsupportedProjectFileError):
            scratch.RawProject.from_project_folder_path(common_testing.get_test_project_path("faulty_json_file"))


class TestRawProjectFunc(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.project = scratch.RawProject.from_project_folder_path(common_testing.get_test_project_path("dancing_castle"))

    def test_can_access_scratch_objects(self):
        for scratch_object in self.project.objects:
            assert scratch_object
            assert isinstance(scratch_object, scratch.Object)
        assert self.project.objects[0].get_objName() == scratch.STAGE_OBJECT_NAME, "Stage object missing"
        assert [_.get_objName() for _ in self.project.objects] == ['Stage', 'Sprite1', 'Cassy Dance']

    def test_can_access_stage_object(self):
        stage_object = self.project.stage_object
        assert stage_object.get_objName() == scratch.STAGE_OBJECT_NAME

    def test_can_access_project_variables(self):
        variables_test_code_content = common.content_of(common_testing.get_test_resources_path("scratch_code_only", "variables_test.json"))
        raw_project = scratch.RawProject.from_project_code_content(variables_test_code_content)
        assert [variable["name"] for variable in raw_project.get_variables()] == ["$", "MarketOpen", "Multiplier", "bc1bought", "bc2bought"]
        # Scratch does not allow local variables for the stage object
        assert raw_project.stage_object.get_variables() == []


class TestObjectInit(unittest.TestCase):

    def setUp(self):
        print _default_object_json_str()
        self.raw_object = json.loads(_default_object_json_str())

    def test_can_construct_on_correct_input(self):
        assert scratch.Object.is_valid_class_input(self.raw_object)
        scratch_object = scratch.Object(self.raw_object)
        assert scratch_object is not None

    def test_fail_on_wrong_input(self):
        del self.raw_object["objName"]
        wrong_raw_object = self.raw_object
        faulty_object_structures = [
            {},
            wrong_raw_object
        ]
        for faulty_input in faulty_object_structures:
            assert not scratch.Object.is_valid_class_input(faulty_input)
            with self.assertRaises(scratch.ObjectError):
                scratch.Object(faulty_input)


class TestObjectFunc(unittest.TestCase):

    def setUp(self):
        self.scratch_object = scratch.Object(json.loads(_default_object_json_str()))

    def test_can_access_scratch_scripts(self):
        scripts = self.scratch_object.scripts
        assert len(scripts) > 1
        for scratch_script in scripts:
            assert scratch_script is not None
            assert isinstance(scratch_script, scratch.Script)

    def test_can_access_scratch_costumes(self):
        assert len(self.scratch_object.get_costumes()) > 1
        for costume in self.scratch_object.get_costumes():
            assert costume is not None
            assert isinstance(costume, dict)
            assert "costumeName" in costume

    def test_can_access_scratch_sounds(self):
        assert len(self.scratch_object.get_sounds()) > 1
        for sound in self.scratch_object.get_sounds():
            assert sound is not None
            assert isinstance(sound, dict)
            assert "soundName" in sound

    def test_can_access_scratch_variables(self):
        assert len(self.scratch_object.get_variables()) > 1
        for variable in self.scratch_object.get_variables():
            assert variable is not None
            assert isinstance(variable, dict)
            assert "name" in variable
            assert "value" in variable


class TestScriptInit(unittest.TestCase):

    def test_can_construct_on_correct_input(self):
        for script_input in EASY_SCRIPTS:
            script = scratch.Script(script_input)
            assert script

    def test_fail_on_wrong_input(self):
        faulty_script_structures = [
            [],
            "a string is no correct input",
            ["the first 2 params", "must be integers", []],
            [0101, 444, "further the third one must be a list"]
        ]
        for faulty_input in faulty_script_structures:
            assert not scratch.Script.is_valid_script_input(faulty_input)
            with self.assertRaises(scratch.ScriptError):
                scratch.Script(faulty_input)


class TestScriptFunc(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.input_data = EASY_SCRIPTS[0]
        self.script = scratch.Script(self.input_data)

    def test_can_access_blocks_from_scratch_script(self):
        assert self.script.get_type() == 'whenGreenFlag'
        expected_block_names = ["say:duration:elapsed:from:", "doRepeat", "changeGraphicEffect:by:", "say:"]
        assert [block[0] for block in self.script.blocks] == expected_block_names
        assert self.script.raw_script == self.input_data[2]



class TestBlockInit(unittest.TestCase):

    def test_can_construct_on_correct_input(self):
        expected_values = (
            (4, (2, 2, 2, 1)),
            (1, (2,)),
            (1, (2,)),
        )
        for script_input, [expected_length, expected_block_children_number] in zip(EASY_SCRIPTS, expected_values):
            assert len(scratch.Script(script_input).blocks) == expected_length
            blocks = scratch.BlockElement.from_raw_script(script_input)
            blocks.prettyprint()
            assert isinstance(blocks, scratch.BlockElement) and blocks.name == "BLOCK_LIST" and len(blocks.children) == expected_length
            nested_blocks = blocks.children
            assert all(isinstance(block, scratch.BlockElement) for block in nested_blocks)
            assert [len(block.children) for block in nested_blocks] == list(expected_block_children_number)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
