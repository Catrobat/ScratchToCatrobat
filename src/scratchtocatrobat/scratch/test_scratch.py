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

import json
import os
import string
import unittest

from scratchtocatrobat.tools import common
from scratchtocatrobat.scratch import scratch
from scratchtocatrobat.tools import common_testing

EASY_SCRIPTS = [
    [23, 125,
        [["whenGreenFlag"],
            ["say:duration:elapsed:from:", "Watch me dance!", 2],
            ["doRepeat", 10, [
                ["forward:", 10],
                ["playDrum", 1, 0.2],
                ["forward:", -10],
                ["playDrum", 1, 0.2]
            ]],
            ["changeGraphicEffect:by:", "color", 25],
            ["say:", "test"], ], ],
    [30, 355, [["whenKeyPressed", "space"], ["changeGraphicEffect:by:", "color", 25]]],
    [30.5, 355.5, [["whenKeyPressed", "space"], ["changeGraphicEffect:by:", "color", 25]]],
]

TEST_PROJECT_FOLDER = "dancing_castle"

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


def create_user_defined_function_workaround_scratch_object(object_data):
    return scratch.Object(object_data)


class ProjectExtractionTest(common_testing.BaseTestCase):
    def test_can_extract_project(self):
        for project_file in common_testing.TEST_PROJECT_FILENAME_TO_ID_MAP:
            common.extract(common_testing.get_test_project_packed_file(project_file), self.temp_dir)
            assert scratch.Project(self.temp_dir)



class TestProjectInit(unittest.TestCase):
    def test_can_construct_on_correct_input(self):
        assert scratch.Project(common_testing.get_test_project_path("simple"), name="dummy", project_id=common_testing.PROJECT_DUMMY_ID)

    def test_fail_on_non_existing_input_path(self):
        with self.assertRaises(EnvironmentError):
            # TODO: check error message
            scratch.Project(common_testing.get_test_project_path("non_existing_path"))

    def test_fail_on_project_with_missing_sound_files(self):
        with self.assertRaises(scratch.ProjectError):
    #         TODO: check error type
            scratch.Project(common_testing.get_test_project_path("missing_sound_resources"), None, None, None, True)

    def test_fail_on_project_with_missing_image_files(self):
        with self.assertRaises(scratch.ProjectError):
            # TODO: check error type
            scratch.Project(common_testing.get_test_project_path("missing_image_resources"), None, None, None, True)


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
        expected_stage_customes_md5_names = set(["510da64cf172d53750dffd23fbf73563.png",
                                                 "033f926829a446a28970f59302b0572d.png"])
        assert set(self.project.background_md5_names) == expected_stage_customes_md5_names

    def test_can_access_listened_pressed_keys(self):
        project = scratch.Project(common_testing.get_test_project_path("keys_pressed"))
        assert project.listened_keys == set([(u'a', 'listenedKeys'), (u'8', 'listenedKeys'), (u'd', 'listenedKeys'), (u'c', 'listenedKeys'), (u'4', 'listenedKeys')])

    def test_can_access_unused_resources_of_project(self):
        project = scratch.Project(common_testing.get_test_project_path("simple"), name="simple", project_id=common_testing.PROJECT_DUMMY_ID)
        assert len(project.unused_resource_paths) > 0
        expected_resources = ['0.png', '2.wav', '3.png', '4.png', '5.png', '6.png', '8.png']
        assert set(map(os.path.basename, project.unused_resource_paths)) == set(expected_resources)


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
        with self.assertRaises((scratch.UnsupportedProjectFileError, scratch.ObjectError)):
            scratch.RawProject.from_project_folder_path(common_testing.get_test_project_path("faulty_json_file"))


class TestRawProjectFunc(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.project = scratch.RawProject.from_project_folder_path(common_testing.get_test_project_path("dancing_castle"))

    def test_can_access_scratch_objects(self):
        for scratch_object in self.project.objects:
            assert scratch_object
            assert isinstance(scratch_object, scratch.Object)
        assert self.project.objects[0].name == scratch.STAGE_OBJECT_NAME, "Stage object missing"
        assert [_.name for _ in self.project.objects] == ['Stage', 'Sprite1', 'Cassy Dance']

    def test_can_access_project_variables(self):
        variables_test_code_content = common.content_of(common_testing.get_test_resources_path("scratch_code_only", "variables_test.json"))
        raw_project = scratch.RawProject.from_project_code_content(variables_test_code_content)
        assert [variable["name"] for variable in raw_project.get_variables()] == ["$", "MarketOpen", "Multiplier", "bc1bought", "bc2bought"]


class TestProjectOrderedObjects(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.project_with_object_indexes = scratch.Project(common_testing.get_test_project_path("dress_up_tera_with_object_indexes"))
        self.project_without_object_indexes = scratch.Project(common_testing.get_test_project_path("dress_up_tera_without_object_indexes"))

    def test_are_scratch_objects_ordered_by_library_index_correctly(self):
        expected_sorted_object_names = ["Stage", "Cape", "Tera", "Mask", "Hat", "Blouse",
                                        "Tshirt", "Wings", "Antennae"]
        assert len(expected_sorted_object_names) == len(self.project_with_object_indexes.objects)
        for idx, scratch_object in enumerate(self.project_with_object_indexes.objects):
            assert scratch_object
            assert isinstance(scratch_object, scratch.Object)
            assert scratch_object.name == expected_sorted_object_names[idx], \
                   "Scratch Object with name '{}' is not equal to '{}'!" \
                   .format(scratch_object.name, expected_sorted_object_names[idx])

    def test_are_scratch_objects_ordered_according_to_given_sequence_when_no_library_index_is_given(self):
        expected_sorted_object_names = ["Stage", "Wings", "Tera", "Antennae", "Blouse", "Tshirt",
                                        "Cape", "Hat", "Mask"]
        assert len(expected_sorted_object_names) == len(self.project_without_object_indexes.objects)
        for idx, scratch_object in enumerate(self.project_without_object_indexes.objects):
            assert scratch_object
            assert isinstance(scratch_object, scratch.Object)
            assert scratch_object.name == expected_sorted_object_names[idx], \
                   "Scratch Object with name '{}' is not equal to '{}'!" \
                   .format(scratch_object.name, expected_sorted_object_names[idx])


class TestObjectInit(unittest.TestCase):

    def setUp(self):
        self.raw_object = json.loads(_default_object_json_str())

    def test_can_construct_on_correct_input(self):
        assert scratch.Object.is_scratch2_project(self.raw_object)
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
            assert not scratch.Object.is_scratch2_project(faulty_input)
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

    def test_fail_with_no_multi_list_on_third_param(self):
        faulty_input = [
            1,
            1,
            [u'']]
        assert not scratch.Script.is_valid_script_input(faulty_input)


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
            blocks = scratch.ScriptElement.from_raw_script(script_input)
            assert isinstance(blocks, scratch.BlockList) and len(blocks.children) == expected_length
            nested_blocks = blocks.children
            assert all(isinstance(block, scratch.ScriptElement) for block in nested_blocks)
            assert [len(block.children) for block in nested_blocks] == list(expected_block_children_number)


class TestScriptElementTree(common_testing.BaseTestCase):

    def test_verify_simple_formula_in_script_element_tree(self):
        script_data = [0, 0, [["whenGreenFlag"], ["wait:elapsed:from:", ["randomFrom:to:", -100, 100]]]]
        expected_raw_script_data = [["whenGreenFlag"], ["wait:elapsed:from:", ["randomFrom:to:", -100, 100]]]

        script = scratch.Script(script_data)
        assert script.type == scratch.SCRIPT_GREEN_FLAG
        assert len(script.arguments) == 0
        assert script.raw_script == expected_raw_script_data
        assert script.blocks == expected_raw_script_data[1:]
        assert isinstance(script.script_element, scratch.BlockList)
        assert script.script_element.name == '<LIST>'
        assert len(script.script_element.children) == 1

        script_element_child = script.script_element.children[0]
        assert script_element_child.name == 'wait:elapsed:from:'
        assert len(script_element_child.children) == 1

        script_element_child = script_element_child.children[0]
        assert script_element_child.name == 'randomFrom:to:'
        assert len(script_element_child.children) == 2

        left_child = script_element_child.children[0]
        right_child = script_element_child.children[1]
        assert left_child.name == -100
        assert len(left_child.children) == 0
        assert right_child.name == 100
        assert len(right_child.children) == 0

    def test_verify_complex_formula_in_script_element_tree(self):
        script_data = [0, 0, [["whenGreenFlag"], ["wait:elapsed:from:", ["+", \
                        0, ["randomFrom:to:", 0, 100]]]]]
        expected_raw_script_data = [["whenGreenFlag"], ["wait:elapsed:from:", ["+", \
                        0, ["randomFrom:to:", 0, 100]]]]

        script = scratch.Script(script_data)
        assert script.type == scratch.SCRIPT_GREEN_FLAG
        assert len(script.arguments) == 0
        assert script.raw_script == expected_raw_script_data
        assert script.blocks == expected_raw_script_data[1:]
        assert isinstance(script.script_element, scratch.BlockList)
        assert script.script_element.name == '<LIST>'
        assert len(script.script_element.children) == 1

        script_element_child = script.script_element.children[0]
        assert script_element_child.name == 'wait:elapsed:from:'
        assert len(script_element_child.children) == 1

        script_element_child = script_element_child.children[0]
        assert script_element_child.name == '+'
        assert len(script_element_child.children) == 2

        left_child = script_element_child.children[0]
        right_child = script_element_child.children[1]
        assert left_child.name == 0
        assert len(left_child.children) == 0
        assert right_child.name == 'randomFrom:to:'
        assert len(right_child.children) == 2

        left_child = right_child.children[0]
        right_child = right_child.children[1]
        assert left_child.name == 0
        assert len(left_child.children) == 0
        assert right_child.name == 100
        assert len(right_child.children) == 0

    def test_verify_complex_script_element_tree(self):
        script_data = [0, 0, [["whenGreenFlag"], ["wait:elapsed:from:", ["+", \
                        0, ["randomFrom:to:", 0, 100]]], ['changeVar:by:', "temp", 0.1]]]
        expected_raw_script_data = [["whenGreenFlag"], ["wait:elapsed:from:", ["+", \
                        0, ["randomFrom:to:", 0, 100]]], ['changeVar:by:', "temp", 0.1]]

        script = scratch.Script(script_data)
        assert script.type == scratch.SCRIPT_GREEN_FLAG
        assert len(script.arguments) == 0
        assert script.raw_script == expected_raw_script_data
        assert script.blocks == expected_raw_script_data[1:]
        assert isinstance(script.script_element, scratch.BlockList)
        assert script.script_element.name == '<LIST>'
        assert len(script.script_element.children) == 2

        script_element_child = script.script_element.children[0]
        assert script_element_child.name == 'wait:elapsed:from:'
        assert len(script_element_child.children) == 1
        script_element_child = script_element_child.children[0]
        assert script_element_child.name == '+'
        assert len(script_element_child.children) == 2

        left_child = script_element_child.children[0]
        right_child = script_element_child.children[1]
        assert left_child.name == 0
        assert len(left_child.children) == 0
        assert right_child.name == 'randomFrom:to:'
        assert len(right_child.children) == 2

        left_child = right_child.children[0]
        right_child = right_child.children[1]
        assert left_child.name == 0
        assert len(left_child.children) == 0
        assert right_child.name == 100
        assert len(right_child.children) == 0

        script_element_child = script.script_element.children[1]
        assert script_element_child.name == 'changeVar:by:'
        assert len(script_element_child.children) == 2

        left_child = script_element_child.children[0]
        right_child = script_element_child.children[1]
        assert left_child.name == 'temp'
        assert len(left_child.children) == 0
        assert right_child.name == 0.1
        assert len(right_child.children) == 0


class TestTimerAndResetTimerBlockWorkarounds(unittest.TestCase):
    TIMER_HELPER_OBJECTS_DATA_TEMPLATE = {
        "objName": "Stage",
        "sounds": [],
        "costumes": [],
        "currentCostumeIndex": 0,
        "penLayerMD5": "5c81a336fab8be57adc039a8a2b33ca9.png",
        "penLayerID": 0,
        "tempoBPM": 60,
        "videoAlpha": 0.5,
        "children": [{ "objName": "Sprite1", "scripts": None }],
        "info": {}
    }

    def setUp(self):
        unittest.TestCase.setUp(self)
        cls = self.__class__
        cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE["scripts"] = []

    def test_timer_block(self):
        cls = self.__class__
        script_data = [0, 0, [["whenGreenFlag"], ["wait:elapsed:from:", ["timer"]]]]
        cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        raw_project = scratch.RawProject(cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE)
        expected_background_object_script_data = [0, 0, [['whenGreenFlag'],
            ['doForever', [
                ['changeVar:by:', scratch.S2CC_TIMER_VARIABLE_NAME, scratch.UPDATE_HELPER_VARIABLE_TIMEOUT],
                ['wait:elapsed:from:', scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
            ]]
        ]]
        expected_first_object_script_data = [0, 0, [["whenGreenFlag"],
            ['wait:elapsed:from:', ['readVariable', scratch.S2CC_TIMER_VARIABLE_NAME]]
        ]]

        # validate
        assert len(raw_project.objects) == 2
        [background_object, first_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 1
        script = background_object.scripts[0]
        expected_script = scratch.Script(expected_background_object_script_data)
        assert script == expected_script

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # global variables
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 1
        assert global_variables[0] == { "name": scratch.S2CC_TIMER_VARIABLE_NAME, "value": 0, "isPersistent": False }

    def test_same_timer_block_twice(self):
        cls = self.__class__
        script_data = [0, 0, [["whenGreenFlag"], ["wait:elapsed:from:", ["timer"]], ["wait:elapsed:from:", ["timer"]]]]
        cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        expected_background_object_script_data = [0, 0, [['whenGreenFlag'],
            ['doForever', [
                ['changeVar:by:', scratch.S2CC_TIMER_VARIABLE_NAME, scratch.UPDATE_HELPER_VARIABLE_TIMEOUT],
                ['wait:elapsed:from:', scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
            ]]
        ]]
        expected_first_object_script_data = [0, 0, [["whenGreenFlag"],
            ['wait:elapsed:from:', ['readVariable', scratch.S2CC_TIMER_VARIABLE_NAME]],
            ['wait:elapsed:from:', ['readVariable', scratch.S2CC_TIMER_VARIABLE_NAME]]
        ]]

        # create project
        raw_project = scratch.RawProject(cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE)

        # validate
        assert len(raw_project.objects) == 2
        [background_object, first_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 1
        script = background_object.scripts[0]
        expected_script = scratch.Script(expected_background_object_script_data)
        assert script == expected_script

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # global variables
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 1
        assert global_variables[0] == { "name": scratch.S2CC_TIMER_VARIABLE_NAME, "value": 0, "isPersistent": False }

    def test_reset_timer_block_with_non_existant_timer_block_should_automatically_add_timer_script(self):
        cls = self.__class__
        expected_background_object_scripts_data = [[0, 0, [['whenGreenFlag'],
            ['doForever', [
                ['changeVar:by:', scratch.S2CC_TIMER_VARIABLE_NAME, scratch.UPDATE_HELPER_VARIABLE_TIMEOUT],
                ['wait:elapsed:from:', scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
            ]]]
        ], [0, 0, [['whenIReceive', scratch.S2CC_TIMER_RESET_BROADCAST_MESSAGE],
            ['setVar:to:', scratch.S2CC_TIMER_VARIABLE_NAME, 0]
        ]]]
        script_data = [0, 0, [["whenGreenFlag"], ["timerReset"]]]
        cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        expected_first_object_script_data = [0, 0, [["whenGreenFlag"],
            ['doBroadcastAndWait', scratch.S2CC_TIMER_RESET_BROADCAST_MESSAGE]
        ]]

        # create project
        raw_project = scratch.RawProject(cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE)

        # validate
        assert len(raw_project.objects) == 2
        [background_object, first_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 2
        script = background_object.scripts[0]
        expected_script = scratch.Script(expected_background_object_scripts_data[0])
        assert script == expected_script
        script = background_object.scripts[1]
        expected_script = scratch.Script(expected_background_object_scripts_data[1])
        assert script == expected_script

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # global variables
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 1
        assert global_variables[0] == { "name": scratch.S2CC_TIMER_VARIABLE_NAME, "value": 0, "isPersistent": False }

    def test_reset_timer_block_with_existant_timer_block_in_same_object_must_NOT_be_ignored(self):
        cls = self.__class__
        expected_background_object_scripts_data = [[0, 0, [['whenGreenFlag'],
            ['doForever', [
                ['changeVar:by:', scratch.S2CC_TIMER_VARIABLE_NAME, scratch.UPDATE_HELPER_VARIABLE_TIMEOUT],
                ['wait:elapsed:from:', scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
            ]]]
        ], [0, 0, [['whenIReceive', scratch.S2CC_TIMER_RESET_BROADCAST_MESSAGE],
            ['setVar:to:', scratch.S2CC_TIMER_VARIABLE_NAME, 0]
        ]]]
        script_data = [0, 0, [["whenGreenFlag"], ["wait:elapsed:from:", ["timer"]], ["timerReset"]]]
        cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        expected_first_object_script_data = [0, 0, [["whenGreenFlag"],
            ['wait:elapsed:from:', ['readVariable', scratch.S2CC_TIMER_VARIABLE_NAME]],
            ["doBroadcastAndWait", scratch.S2CC_TIMER_RESET_BROADCAST_MESSAGE]
        ]]

        # create project
        raw_project = scratch.RawProject(cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE)

        # validate
        assert len(raw_project.objects) == 2
        [background_object, first_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 2
        script = background_object.scripts[0]
        expected_script = scratch.Script(expected_background_object_scripts_data[0])
        assert script == expected_script
        script = background_object.scripts[1]
        expected_script = scratch.Script(expected_background_object_scripts_data[1])
        assert script == expected_script

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # global variables
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 1
        assert global_variables[0] == { "name": scratch.S2CC_TIMER_VARIABLE_NAME, "value": 0, "isPersistent": False }

    def test_reset_timer_block_and_timer_block_within_loop_must_NOT_be_ignored(self):
        cls = self.__class__
        expected_background_object_scripts_data = [[0, 0, [['whenGreenFlag'],
            ['doForever', [
                ['changeVar:by:', scratch.S2CC_TIMER_VARIABLE_NAME, scratch.UPDATE_HELPER_VARIABLE_TIMEOUT],
                ['wait:elapsed:from:', scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
            ]]]
        ], [0, 0, [['whenIReceive', scratch.S2CC_TIMER_RESET_BROADCAST_MESSAGE],
            ['setVar:to:', scratch.S2CC_TIMER_VARIABLE_NAME, 0]
        ]]]
        script_data = [0, 0, [["whenGreenFlag"],
            ["doRepeat", 100, [["wait:elapsed:from:", ["timer"]], ["timerReset"]]]]
        ]
        cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        expected_first_object_script_data = [0, 0, [["whenGreenFlag"],
            ["doRepeat", 100, [
                ['wait:elapsed:from:', ['readVariable', scratch.S2CC_TIMER_VARIABLE_NAME]],
                ["doBroadcastAndWait", scratch.S2CC_TIMER_RESET_BROADCAST_MESSAGE]]
        ]]]

        # create project
        raw_project = scratch.RawProject(cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE)

        # validate
        assert len(raw_project.objects) == 2
        [background_object, first_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 2
        script = background_object.scripts[0]
        expected_script = scratch.Script(expected_background_object_scripts_data[0])
        assert script == expected_script
        script = background_object.scripts[1]
        expected_script = scratch.Script(expected_background_object_scripts_data[1])
        assert script == expected_script

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # global variables
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 1
        assert global_variables[0] == { "name": scratch.S2CC_TIMER_VARIABLE_NAME, "value": 0, "isPersistent": False }

    def test_reset_timer_block_with_existant_timer_block_in_other_object_must_NOT_be_ignored(self):
        cls = self.__class__
        background_script_data = [0, 0, [["whenGreenFlag"], ["timerReset"]]]
        cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE["scripts"] = [background_script_data]
        expected_background_object_scripts_data = [[0, 0, [['whenGreenFlag'],
            ["doBroadcastAndWait", scratch.S2CC_TIMER_RESET_BROADCAST_MESSAGE]
        ]], [0, 0, [['whenGreenFlag'],
            ['doForever', [
                ['changeVar:by:', scratch.S2CC_TIMER_VARIABLE_NAME, scratch.UPDATE_HELPER_VARIABLE_TIMEOUT],
                ['wait:elapsed:from:', scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
            ]]]
        ], [0, 0, [['whenIReceive', scratch.S2CC_TIMER_RESET_BROADCAST_MESSAGE],
            ['setVar:to:', scratch.S2CC_TIMER_VARIABLE_NAME, 0]
        ]]]

        # first object scripts
        first_object_script_data = [0, 0, [["whenGreenFlag"], ["wait:elapsed:from:", ["timer"]]]]
        cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [first_object_script_data]
        expected_first_object_script_data = [0, 0, [["whenGreenFlag"],
            ['wait:elapsed:from:', ['readVariable', scratch.S2CC_TIMER_VARIABLE_NAME]]
        ]]

        # create project
        raw_project = scratch.RawProject(cls.TIMER_HELPER_OBJECTS_DATA_TEMPLATE)

        # validate
        assert len(raw_project.objects) == 2
        [background_object, first_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 3
        script = background_object.scripts[0]
        expected_script = scratch.Script(expected_background_object_scripts_data[0])
        assert script == expected_script
        script = background_object.scripts[1]
        expected_script = scratch.Script(expected_background_object_scripts_data[1])
        assert script == expected_script
        script = background_object.scripts[2]
        expected_script = scratch.Script(expected_background_object_scripts_data[2])
        assert script == expected_script

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # global variables
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 1
        assert global_variables[0] == { "name": scratch.S2CC_TIMER_VARIABLE_NAME, "value": 0, "isPersistent": False }

class TestKeyPressedWorkaround(unittest.TestCase):
    KEYPRESSED_HELPER_OBJECTS_DATA_TEMPLATE = {
        "objName": "Stage",
        "sounds": [],
        "costumes": [],
        "currentCostumeIndex": 0,
        "penLayerMD5": "5c81a336fab8be57adc039a8a2b33ca9.png",
        "penLayerID": 0,
        "tempoBPM": 60,
        "videoAlpha": 0.5,
        "children": [{ "objName": "Sprite1", "scripts": None }],
        "info": {}
    }

    def setUp(self):
        unittest.TestCase.setUp(self)
        cls = self.__class__
        cls.KEYPRESSED_HELPER_OBJECTS_DATA_TEMPLATE["scripts"] = []

    def test_key_pressed(self):
        cls = self.__class__
        script_data = [0,0,[["whenGreenFlag"],["doForever", [["doIf", ["keyPressed:", "w"],[["changeYposBy:", 1]]]]]]]
        cls.KEYPRESSED_HELPER_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        raw_project = scratch.RawProject(cls.KEYPRESSED_HELPER_OBJECTS_DATA_TEMPLATE)
        key_pressed_var_name = scratch.S2CC_KEY_VARIABLE_NAME + "w"
        expected_first_object_script_data = [0,0,[["whenGreenFlag"],["doForever", [["doIf", ["readVariable", key_pressed_var_name],[["changeYposBy:", 1]]]]]]]

        # validate
        assert len(raw_project.objects) == 2
        [background_object, sprite_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 0

        script = sprite_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

class TestDistanceBlockWorkaround(unittest.TestCase):
    DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE = {
        "objName": "Stage",
        "sounds": [],
        "costumes": [],
        "currentCostumeIndex": 0,
        "penLayerMD5": "5c81a336fab8be57adc039a8a2b33ca9.png",
        "penLayerID": 0,
        "tempoBPM": 60,
        "videoAlpha": 0.5,
        "children": [{ "objName": "Sprite1", "scripts": None },
                     { "objName": "Sprite2", "scripts": None }],
        "info": {}
    }

    def setUp(self):
        unittest.TestCase.setUp(self)
        cls = self.__class__
        cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE["scripts"] = []

    def test_single_distance_block(self):
        cls = self.__class__
        script_data = [0, 0, [["whenGreenFlag"], ["forward:", ["distanceTo:", "Sprite2"]]]]
        cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE["children"][1]["scripts"] = []
        raw_project = scratch.RawProject(cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE)
        position_x_var_name = scratch.S2CC_POSITION_X_VARIABLE_NAME_PREFIX + "Sprite2"
        position_y_var_name = scratch.S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + "Sprite2"
        expected_first_object_script_data = [0, 0, [["whenGreenFlag"], ['forward:',
            ["computeFunction:of:", "sqrt", ["+",
              ["*",
                ["()", ["-", ["xpos"], ["readVariable", position_x_var_name]]],
                ["()", ["-", ["xpos"], ["readVariable", position_x_var_name]]]
              ], ["*",
                ["()", ["-", ["ypos"], ["readVariable", position_y_var_name]]],
                ["()", ["-", ["ypos"], ["readVariable", position_y_var_name]]]
              ]
            ]]
        ]]]
        expected_second_object_script_data = [0, 0, [['whenGreenFlag'],
            ["doForever", [
              ["setVar:to:", position_x_var_name, ["xpos"]],
              ["setVar:to:", position_y_var_name, ["ypos"]],
              ["wait:elapsed:from:", scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
            ]]
        ]]

        # validate
        assert len(raw_project.objects) == 3
        [background_object, first_object, second_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 0

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # second object
        assert len(second_object.scripts) == 1
        script = second_object.scripts[0]
        expected_script = scratch.Script(expected_second_object_script_data)
        assert script == expected_script

        # global variables
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 2
        assert global_variables[0] == { "name": position_x_var_name, "value": 0, "isPersistent": False }
        assert global_variables[1] == { "name": position_y_var_name, "value": 0, "isPersistent": False }

    def test_two_distance_blocks_in_same_object(self):
        cls = self.__class__
        script_data = [0, 0, [["whenGreenFlag"], ["forward:", ["distanceTo:", "Sprite2"]],
                              ["forward:", ["distanceTo:", "Sprite2"]]]]
        cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE["children"][1]["scripts"] = []
        raw_project = scratch.RawProject(cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE)
        position_x_var_name = scratch.S2CC_POSITION_X_VARIABLE_NAME_PREFIX + "Sprite2"
        position_y_var_name = scratch.S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + "Sprite2"
        expected_first_object_script_data = [0, 0, [["whenGreenFlag"], ['forward:',
            ["computeFunction:of:", "sqrt", ["+",
              ["*",
                ["()", ["-", ["xpos"], ["readVariable", position_x_var_name]]],
                ["()", ["-", ["xpos"], ["readVariable", position_x_var_name]]]
              ], ["*",
                ["()", ["-", ["ypos"], ["readVariable", position_y_var_name]]],
                ["()", ["-", ["ypos"], ["readVariable", position_y_var_name]]]
              ]
            ]]
        ], ['forward:',
            ["computeFunction:of:", "sqrt", ["+",
              ["*",
                ["()", ["-", ["xpos"], ["readVariable", position_x_var_name]]],
                ["()", ["-", ["xpos"], ["readVariable", position_x_var_name]]]
              ], ["*",
                ["()", ["-", ["ypos"], ["readVariable", position_y_var_name]]],
                ["()", ["-", ["ypos"], ["readVariable", position_y_var_name]]]
              ]
            ]]
        ]]]
        expected_second_object_script_data = [0, 0, [['whenGreenFlag'],
            ["doForever", [
              ["setVar:to:", position_x_var_name, ["xpos"]],
              ["setVar:to:", position_y_var_name, ["ypos"]],
              ["wait:elapsed:from:", scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
            ]]
        ]]

        # validate
        assert len(raw_project.objects) == 3
        [background_object, first_object, second_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 0

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # second object
        assert len(second_object.scripts) == 1
        script = second_object.scripts[0]
        expected_script = scratch.Script(expected_second_object_script_data)
        assert script == expected_script

        # global variables
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 2
        assert global_variables[0] == { "name": position_x_var_name, "value": 0, "isPersistent": False }
        assert global_variables[1] == { "name": position_y_var_name, "value": 0, "isPersistent": False }

    def test_two_distance_blocks_in_different_objects(self):
        cls = self.__class__
        script_data = [0, 0, [["whenGreenFlag"], ["forward:", ["distanceTo:", "Sprite2"]]]]
        cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE["scripts"] = [script_data]
        cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE["children"][1]["scripts"] = []
        raw_project = scratch.RawProject(cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE)
        position_x_var_name = scratch.S2CC_POSITION_X_VARIABLE_NAME_PREFIX + "Sprite2"
        position_y_var_name = scratch.S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + "Sprite2"
        expected_background_and_first_object_script_data = [0, 0, [["whenGreenFlag"], ['forward:',
            ["computeFunction:of:", "sqrt", ["+",
              ["*",
                ["()", ["-", ["xpos"], ["readVariable", position_x_var_name]]],
                ["()", ["-", ["xpos"], ["readVariable", position_x_var_name]]]
              ], ["*",
                ["()", ["-", ["ypos"], ["readVariable", position_y_var_name]]],
                ["()", ["-", ["ypos"], ["readVariable", position_y_var_name]]]
              ]
            ]]
        ]]]
        expected_second_object_script_data = [0, 0, [['whenGreenFlag'],
            ["doForever", [
              ["setVar:to:", position_x_var_name, ["xpos"]],
              ["setVar:to:", position_y_var_name, ["ypos"]],
              ["wait:elapsed:from:", scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
            ]]
        ]]

        # validate
        assert len(raw_project.objects) == 3
        [background_object, first_object, second_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 1
        script = background_object.scripts[0]
        expected_script = scratch.Script(expected_background_and_first_object_script_data)
        assert script == expected_script

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_background_and_first_object_script_data)
        assert script == expected_script

        # second object
        assert len(second_object.scripts) == 1
        script = second_object.scripts[0]
        expected_script = scratch.Script(expected_second_object_script_data)
        assert script == expected_script

        # global variables
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 2
        assert global_variables[0] == { "name": position_x_var_name, "value": 0, "isPersistent": False }
        assert global_variables[1] == { "name": position_y_var_name, "value": 0, "isPersistent": False }

    def test_two_different_distance_blocks_in_different_objects(self):
        cls = self.__class__
        script_data0 = [0, 0, [["whenGreenFlag"], ["forward:", ["distanceTo:", "Sprite2"]]]]
        script_data2 = [0, 0, [["whenGreenFlag"], ["forward:", ["distanceTo:", "Sprite1"]]]]
        cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE["scripts"] = [script_data0]
        cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = []
        cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE["children"][1]["scripts"] = [script_data2]
        raw_project = scratch.RawProject(cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE)
        position_x_var_name1 = scratch.S2CC_POSITION_X_VARIABLE_NAME_PREFIX + "Sprite1"
        position_y_var_name1 = scratch.S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + "Sprite1"
        position_x_var_name2 = scratch.S2CC_POSITION_X_VARIABLE_NAME_PREFIX + "Sprite2"
        position_y_var_name2 = scratch.S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + "Sprite2"
        expected_background_object_script_data = [0, 0, [["whenGreenFlag"], ['forward:',
            ["computeFunction:of:", "sqrt", ["+",
              ["*",
                ["()", ["-", ["xpos"], ["readVariable", position_x_var_name2]]],
                ["()", ["-", ["xpos"], ["readVariable", position_x_var_name2]]]
              ], ["*",
                ["()", ["-", ["ypos"], ["readVariable", position_y_var_name2]]],
                ["()", ["-", ["ypos"], ["readVariable", position_y_var_name2]]]
              ]
            ]]
        ]]]
        expected_first_object_script_data = [0, 0, [['whenGreenFlag'],
            ["doForever", [
              ["setVar:to:", position_x_var_name1, ["xpos"]],
              ["setVar:to:", position_y_var_name1, ["ypos"]],
              ["wait:elapsed:from:", scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
            ]]
        ]]
        expected_second_object_scripts_data = [[0, 0, [["whenGreenFlag"], ['forward:',
            ["computeFunction:of:", "sqrt", ["+",
              ["*",
                ["()", ["-", ["xpos"], ["readVariable", position_x_var_name1]]],
                ["()", ["-", ["xpos"], ["readVariable", position_x_var_name1]]]
              ], ["*",
                ["()", ["-", ["ypos"], ["readVariable", position_y_var_name1]]],
                ["()", ["-", ["ypos"], ["readVariable", position_y_var_name1]]]
              ]
            ]]
        ]]], [0, 0, [['whenGreenFlag'],
            ["doForever", [
              ["setVar:to:", position_x_var_name2, ["xpos"]],
              ["setVar:to:", position_y_var_name2, ["ypos"]],
              ["wait:elapsed:from:", scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
            ]]
        ]]]

        # validate
        assert len(raw_project.objects) == 3
        [background_object, first_object, second_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 1
        script = background_object.scripts[0]
        expected_script = scratch.Script(expected_background_object_script_data)
        assert script == expected_script

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # second object
        assert len(second_object.scripts) == 2
        script = second_object.scripts[0]
        expected_script = scratch.Script(expected_second_object_scripts_data[0])
        assert script == expected_script
        script = second_object.scripts[1]
        expected_script = scratch.Script(expected_second_object_scripts_data[1])
        assert script == expected_script

        # global variables
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 4
        assert global_variables[0] == { "name": position_x_var_name2, "value": 0, "isPersistent": False }
        assert global_variables[1] == { "name": position_y_var_name2, "value": 0, "isPersistent": False }
        assert global_variables[2] == { "name": position_x_var_name1, "value": 0, "isPersistent": False }
        assert global_variables[3] == { "name": position_y_var_name1, "value": 0, "isPersistent": False }

    def test_single_distance_block_to_mouse_pointer(self):
        cls = self.__class__
        script_data = [0, 0, [["whenGreenFlag"], ["forward:", ["distanceTo:", "_mouse_"]]]]
        cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE["children"][1]["scripts"] = []
        raw_project = scratch.RawProject(cls.DISTANCE_HELPER_OBJECTS_DATA_TEMPLATE)
        position_x_var_name = scratch.S2CC_POSITION_X_VARIABLE_NAME_PREFIX + "_mouse_"
        position_y_var_name = scratch.S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + "_mouse_"
        expected_first_object_script_data = [0, 0, [["whenGreenFlag"], ["forward:",
            ["computeFunction:of:", "sqrt",
                ["+",
                    ["*",
                        ["()", ["-", ["xpos"], ["readVariable", position_x_var_name]]],
                        ["()", ["-", ["xpos"], ["readVariable", position_x_var_name]]]
                    ],
                    ["*",
                        ["()", ["-", ["ypos"], ["readVariable", position_y_var_name]]],
                        ["()", ["-", ["ypos"], ["readVariable", position_y_var_name]]]
                    ]
                 ]]
            ]]]


        # validate
        assert len(raw_project.objects) == 3
        [background_object, first_object, second_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 0

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # mouse-sprite will be created during conversion and not in the pre-processing ->
        # for now, the second sprite is irrelevant
        assert len(second_object.scripts) == 0

        # global variables; for the mouse-pointer workaround, the variables are created during conversion
        # and not in the pre-process
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 0

        # check the flag -> indicates that mouse-sprite has to be created during conversion
        assert raw_project._has_mouse_position_script

class TestGlideToObjectBlockWorkaround(unittest.TestCase):
    GLIDE_TO_OBJECTS_DATA_TEMPLATE = {
        "objName": "Stage",
        "sounds": [],
        "costumes": [],
        "currentCostumeIndex": 0,
        "penLayerMD5": "5c81a336fab8be57adc039a8a2b33ca9.png",
        "penLayerID": 0,
        "tempoBPM": 60,
        "videoAlpha": 0.5,
        "children": [{ "objName": "Sprite1", "scripts": None },
                     { "objName": "Sprite2", "scripts": None }],
        "info": {}
    }

    def setUp(self):
        unittest.TestCase.setUp(self)
        cls = self.__class__
        cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE["scripts"] = []

    def test_glide_to_different_sprite(self):
        cls = self.__class__
        spinner_selection = "Sprite2"
        time_in_sec = "1"
        script_data = [0, 0, [["whenGreenFlag"], ["glideTo:", time_in_sec, spinner_selection]]]
        cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE["children"][1]["scripts"] = []
        raw_project = scratch.RawProject(cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE)

        position_x_var_name = scratch.S2CC_POSITION_X_VARIABLE_NAME_PREFIX + spinner_selection
        position_y_var_name = scratch.S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + spinner_selection
        expected_first_object_script_data = \
            [0, 0, [["whenGreenFlag"], [
                "glideSecs:toX:y:elapsed:from:",
                 time_in_sec,
                ["readVariable", position_x_var_name],
                ["readVariable", position_y_var_name]
            ]]]

        expected_second_object_script_data = \
            [0, 0, [["whenGreenFlag"],[
                    "doForever", [
                        ["setVar:to:", position_x_var_name, ["xpos"]],
                        ["setVar:to:", position_y_var_name, ["ypos"]],
                        ["wait:elapsed:from:", scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
                 ]]
            ]]

        # validate
        assert len(raw_project.objects) == 3
        [background_object, first_object, second_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 0

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # second object
        assert len(second_object.scripts) == 1
        script = second_object.scripts[0]
        expected_script = scratch.Script(expected_second_object_script_data)
        assert script == expected_script

        # global variables
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 2
        assert global_variables[0] == { "name": position_x_var_name, "value": 0, "isPersistent": False }
        assert global_variables[1] == { "name": position_y_var_name, "value": 0, "isPersistent": False }

    def test_glide_to_random_position(self):
        cls = self.__class__
        spinner_selection = "_random_"
        time_in_sec = "1"
        script_data = [0, 0, [["whenGreenFlag"], ["glideTo:", time_in_sec, spinner_selection]]]
        cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE["children"][1]["scripts"] = []
        raw_project = scratch.RawProject(cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE)

        # random position also needs a workaround -> different resolutions in scratch and pocket code
        left_x, right_x = -scratch.STAGE_WIDTH_IN_PIXELS / 2, scratch.STAGE_WIDTH_IN_PIXELS / 2
        lower_y, upper_y = -scratch.STAGE_HEIGHT_IN_PIXELS / 2, scratch.STAGE_HEIGHT_IN_PIXELS / 2

        expected_first_object_script_data = \
            [0, 0, [["whenGreenFlag"],[
                "glideSecs:toX:y:elapsed:from:",
                time_in_sec,
                ["randomFrom:to:", left_x, right_x],
                ["randomFrom:to:", lower_y, upper_y]
            ]]]

        # validate
        assert len(raw_project.objects) == 3
        [background_object, first_object, second_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 0

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # second object
        assert len(second_object.scripts) == 0

    def test_glide_to_mouse_poointer(self):
        cls = self.__class__
        spinner_selection = "_mouse_"
        time_in_sec = "1"
        script_data = [0, 0, [["whenGreenFlag"], ["glideTo:", time_in_sec, spinner_selection]]]
        cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE["children"][1]["scripts"] = []
        raw_project = scratch.RawProject(cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE)

        position_x_var_name = scratch.S2CC_POSITION_X_VARIABLE_NAME_PREFIX + spinner_selection
        position_y_var_name = scratch.S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + spinner_selection
        expected_first_object_script_data = \
            [0, 0, [["whenGreenFlag"], [
                "glideSecs:toX:y:elapsed:from:",
                time_in_sec,
                ["readVariable", position_x_var_name],
                ["readVariable", position_y_var_name]
            ]]]

        # validate
        assert len(raw_project.objects) == 3
        [background_object, first_object, second_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 0

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # same as in the 'distanceTo'-block workaround, the mouse-sprite is created during
        # conversion and not in the pre-processing -> no mouse-sprite yet
        assert len(second_object.scripts) == 0

        # global variables; for the mouse-pointer workaround, the variables are created during conversion
        # and not in the pre-process
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 0

        # check the flag -> indicates that mouse-sprite has to be created during conversion
        assert raw_project._has_mouse_position_script

    def test_glide_to_random_single_nested(self):
        cls = self.__class__
        spinner_selection = "_random_"
        time_in_sec = "1"
        script_data = [0, 0, [["whenGreenFlag"], ["doForever", ["glideTo:", time_in_sec, spinner_selection]]]]
        cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE["children"][1]["scripts"] = []
        raw_project = scratch.RawProject(cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE)

        # random position also needs a workaround -> different resolutions in scratch and pocket code
        left_x, right_x = -scratch.STAGE_WIDTH_IN_PIXELS / 2, scratch.STAGE_WIDTH_IN_PIXELS / 2
        lower_y, upper_y = -scratch.STAGE_HEIGHT_IN_PIXELS / 2, scratch.STAGE_HEIGHT_IN_PIXELS / 2

        expected_first_object_script_data = \
            [0, 0, [["whenGreenFlag"],
                ["doForever",
                    ["glideSecs:toX:y:elapsed:from:",
                        time_in_sec,
                        ["randomFrom:to:", left_x, right_x],
                        ["randomFrom:to:", lower_y, upper_y]
                    ]
                ]
            ]]

        # validate
        assert len(raw_project.objects) == 3
        [background_object, first_object, second_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 0

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # second object
        assert len(second_object.scripts) == 0

    def test_glide_to_objects_double_nested(self):
        cls = self.__class__
        spinner_selection_random = "_random_"
        spinner_selection_mouse = "_mouse_"
        time_in_sec = "1"

        script_data = [0, 0, [["whenGreenFlag"],
                                ["doForever",
                                    ["doIfElse", [">", ["randomFrom:to:", 1.0, 100.0], "50"],
                                        ["glideTo:", time_in_sec, spinner_selection_random],
                                        ["glideTo:", time_in_sec, spinner_selection_mouse]
                                    ]
                                ]
                            ]]
        cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE["children"][0]["scripts"] = [script_data]
        cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE["children"][1]["scripts"] = []
        raw_project = scratch.RawProject(cls.GLIDE_TO_OBJECTS_DATA_TEMPLATE)

        # variables for x and y positions of the mouse-pointer
        position_x_var_name = scratch.S2CC_POSITION_X_VARIABLE_NAME_PREFIX + spinner_selection_mouse
        position_y_var_name = scratch.S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + spinner_selection_mouse

        # random position option also needs a workaround -> different resolutions in scratch and pocket code
        left_x, right_x = -scratch.STAGE_WIDTH_IN_PIXELS / 2, scratch.STAGE_WIDTH_IN_PIXELS / 2
        lower_y, upper_y = -scratch.STAGE_HEIGHT_IN_PIXELS / 2, scratch.STAGE_HEIGHT_IN_PIXELS / 2

        expected_first_object_script_data = \
            [0, 0, [["whenGreenFlag"],
                    ["doForever",
                        ["doIfElse", [">", ["randomFrom:to:", 1.0, 100.0], "50"],
                            ["glideSecs:toX:y:elapsed:from:",
                                time_in_sec,
                                ["randomFrom:to:", left_x, right_x],
                                ["randomFrom:to:", lower_y, upper_y]
                            ],
                            ["glideSecs:toX:y:elapsed:from:",
                                time_in_sec,
                                ["readVariable", position_x_var_name],
                                ["readVariable", position_y_var_name]
                            ]
                        ]
                    ]
            ]]

        # validate
        assert len(raw_project.objects) == 3
        [background_object, first_object, second_object] = raw_project.objects

        # background object
        assert len(background_object.scripts) == 0

        # first object
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_script_data)
        assert script == expected_script

        # second object
        assert len(second_object.scripts) == 0


class TestShowSensorBlockWorkarounds(unittest.TestCase):
    SENSOR_HELPER_OBJECTS_DATA_TEMPLATE = {
        "objName": "Stage",
        "sounds": [],
        "costumes": [],
        "currentCostumeIndex": 0,
        "penLayerMD5": "5c81a336fab8be57adc039a8a2b33ca9.png",
        "penLayerID": 0,
        "tempoBPM": 60,
        "videoAlpha": 0.5,
        "children": [{ "objName": "Sprite1", "scripts": [] }],
        "info": {}
    }

    def setUp(self):
        unittest.TestCase.setUp(self)
        cls = self.__class__
        cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["scripts"] = []
        self.original_child_objects = cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"][:]

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        cls = self.__class__
        cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"] = self.original_child_objects[:]

    def test_convert_show_sensor_without_parameter_block(self):
        cls = self.__class__
        sprite_name = "Sprite1"
        original_child_objects = cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"]
        for command_name in ["xpos", "ypos", "heading", "costumeIndex", "scale"]:
            cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"] = original_child_objects[:]
            cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"] += [{
                "target": sprite_name,
                "cmd": command_name,
                "param": None,
                "visible": True
            }]

            raw_project = scratch.RawProject(cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE)
            variable_name = scratch.S2CC_SENSOR_PREFIX + "{}_{}".format(sprite_name, command_name)
            expected_first_object_script_data = [0, 0, [['whenGreenFlag'],
                ['doForever', [
                    ["setVar:to:", variable_name, [command_name]],
                    ["wait:elapsed:from:", scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
                ]]
            ]]

            # validate
            assert len(raw_project.objects) == 2
            [background_object, first_object] = raw_project.objects

            # scripts of sprite objects
            assert len(background_object.scripts) == 0
            assert len(first_object.scripts) == 1
            script = first_object.scripts[0]
            expected_script = scratch.Script(expected_first_object_script_data)
            assert script == expected_script

            # sprite variables
            assert len(background_object._dict_object["variables"]) == 0
            first_object_variables = first_object._dict_object["variables"]
            assert len(first_object_variables) == 1
            assert first_object_variables[0] == { "name": variable_name, "value": 0, "isPersistent": False }

    def test_convert_show_sensor_with_parameter_block(self):
        cls = self.__class__
        sprite_name = "Sprite1"
        original_child_objects = cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"]
        for command_name, param in [("timeAndDate", "minute"), ("timeAndDate", "second")]:
            cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"] = original_child_objects[:]
            cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"] += [{
                "target": sprite_name,
                "cmd": command_name,
                "param": param,
                "visible": True
            }]

            raw_project = scratch.RawProject(cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE)
            variable_name = scratch.S2CC_SENSOR_PREFIX + "{}_{}{}".format(sprite_name, command_name, "_" + param if param else "")
            expected_first_object_script_data = [0, 0, [['whenGreenFlag'],
                ['doForever', [
                    ["setVar:to:", variable_name, [command_name, param]],
                    ["wait:elapsed:from:", scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
                ]]
            ]]

            # validate
            assert len(raw_project.objects) == 2
            [background_object, first_object] = raw_project.objects

            # scripts of sprite objects
            assert len(background_object.scripts) == 0
            assert len(first_object.scripts) == 1
            script = first_object.scripts[0]
            expected_script = scratch.Script(expected_first_object_script_data)
            assert script == expected_script

            # sprite variables
            assert len(background_object._dict_object["variables"]) == 0
            first_object_variables = first_object._dict_object["variables"]
            assert len(first_object_variables) == 1
            assert first_object_variables[0] == { "name": variable_name, "value": 0, "isPersistent": False }

    def test_convert_stage_specific_show_sensor_without_parameter_block(self):
        cls = self.__class__
        sprite_name = "Stage"
        original_child_objects = cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"]
        for command_name in ["xpos", "ypos", "heading", "costumeIndex", "scale"]:
            cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"] = original_child_objects[:]
            cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"] += [{
                "target": sprite_name,
                "cmd": command_name,
                "param": None,
                "visible": True
            }]

            raw_project = scratch.RawProject(cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE)
            variable_name = scratch.S2CC_SENSOR_PREFIX + "{}_{}".format(sprite_name, command_name)
            expected_stage_object_script_data = [0, 0, [['whenGreenFlag'],
                ['doForever', [
                    ["setVar:to:", variable_name, [command_name]],
                    ["wait:elapsed:from:", scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
                ]]
            ]]

            # validate
            assert len(raw_project.objects) == 2
            [background_object, first_object] = raw_project.objects

            # scripts of sprite objects
            assert len(first_object.scripts) == 0
            assert len(background_object.scripts) == 1
            script = background_object.scripts[0]
            expected_script = scratch.Script(expected_stage_object_script_data)
            assert script == expected_script

            # sprite variables
            assert len(first_object._dict_object["variables"]) == 0
            stage_object_variables = background_object._dict_object["variables"]
            assert len(stage_object_variables) == 1
            assert stage_object_variables[0] == { "name": variable_name, "value": 0, "isPersistent": False }

    def test_convert_stage_specific_show_sensor_with_parameter_block(self):
        cls = self.__class__
        sprite_name = "Stage"
        original_child_objects = cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"]
        for command_name, param in [("timeAndDate", "minute"), ("timeAndDate", "second")]:
            cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"] = original_child_objects[:]
            cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE["children"] += [{
                "target": sprite_name,
                "cmd": command_name,
                "param": param,
                "visible": True
            }]

            raw_project = scratch.RawProject(cls.SENSOR_HELPER_OBJECTS_DATA_TEMPLATE)
            variable_name = scratch.S2CC_SENSOR_PREFIX + "{}_{}{}".format(sprite_name, command_name, "_" + param if param else "")
            expected_stage_object_script_data = [0, 0, [['whenGreenFlag'],
                ['doForever', [
                    ["setVar:to:", variable_name, [command_name, param]],
                    ["wait:elapsed:from:", scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
                ]]
            ]]

            # validate
            assert len(raw_project.objects) == 2
            [background_object, first_object] = raw_project.objects

            # scripts of sprite objects
            assert len(first_object.scripts) == 0
            assert len(background_object.scripts) == 1
            script = background_object.scripts[0]
            expected_script = scratch.Script(expected_stage_object_script_data)
            assert script == expected_script

            # sprite variables
            assert len(first_object._dict_object["variables"]) == 0
            stage_object_variables = background_object._dict_object["variables"]
            assert len(stage_object_variables) == 1
            assert stage_object_variables[0] == { "name": variable_name, "value": 0, "isPersistent": False }


class TestGetAttributeBlockWorkarounds(unittest.TestCase):

    ATTRIBUTE_NAME_TO_SENSOR_NAME_MAP = {
        "x position": "xpos",
        "y position": "ypos",
        "direction": "heading",
        "costume #": "costumeIndex",
        "costume name": "costumeName",
        "size": "scale",
        "volume": "volume"
    }

    def setUp(self):
        unittest.TestCase.setUp(self)
        cls = self.__class__
        self.root_info = {
            "objName": "Stage",
            "sounds": [],
            "costumes": [],
            "currentCostumeIndex": 0,
            "penLayerMD5": "5c81a336fab8be57adc039a8a2b33ca9.png",
            "penLayerID": 0,
            "tempoBPM": 60,
            "videoAlpha": 0.5,
            "children": [{ "objName": "Sprite1", "scripts": [] }],
            "scripts": [],
            "variables": [{ "name": "result", "value": 1, "isPersistent": False }],
            "info": {}
        }

    def test_convert_global_variable_attribute_block(self):
        cls = self.__class__
        variable_name = "result"
        first_script_data = [0, 0, [["whenGreenFlag"],
            ["wait:elapsed:from:", 2],
            ["setVar:to:", "result", ["getAttribute:of:", variable_name, "_stage_"]]
        ]]
        self.root_info["children"][0]["scripts"] = [first_script_data]
        raw_project = scratch.RawProject(self.root_info)
        first_script_data[2][2][2] = ["readVariable", variable_name]
        expected_first_object_first_script_data = first_script_data

        # validate
        assert len(raw_project.objects) == 2
        [background_object, first_object] = raw_project.objects

        # scripts of sprite objects
        assert len(background_object.scripts) == 0
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_first_script_data)
        assert script == expected_script

        # sprite variables
        global_variables = background_object._dict_object["variables"]
        assert len(global_variables) == 1
        assert len(first_object._dict_object["variables"]) == 0
        assert global_variables[0] == { "name": variable_name, "value": 1, "isPersistent": False }

    def test_convert_local_variable_of_same_object_attribute_block(self):
        cls = self.__class__
        sprite_name = "Sprite1"
        variable_name = "localVariable"
        first_script_data = [0, 0, [["whenGreenFlag"],
            ["wait:elapsed:from:", 2],
            ["setVar:to:", "result", ["getAttribute:of:", variable_name, sprite_name]]
        ]]
        self.root_info["children"][0]["scripts"] = [first_script_data]
        self.root_info["children"][0]["variables"] = [{ "name": variable_name, "value": 0, "isPersistent": False }]
        raw_project = scratch.RawProject(self.root_info)
        first_script_data[2][2][2] = ["readVariable", variable_name]
        expected_first_object_first_script_data = first_script_data

        # validate
        assert len(raw_project.objects) == 2
        [background_object, first_object] = raw_project.objects

        # scripts of sprite objects
        assert len(background_object.scripts) == 0
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_first_script_data)
        assert script == expected_script

        # sprite variables
        global_variables = background_object._dict_object["variables"]
        first_object_variables = first_object._dict_object["variables"]
        assert len(global_variables) == 1
        assert len(first_object_variables) == 1
        assert global_variables[0] == { "name": "result", "value": 1, "isPersistent": False }
        assert first_object_variables[0] == { "name": variable_name, "value": 0, "isPersistent": False }

    def test_convert_local_variable_of_other_object_attribute_block(self):
        cls = self.__class__
        sprite_name_of_other_object = "Sprite2"
        variable_name = "localVariableOfSprite2"
        self.root_info["children"] += [{
            "objName": sprite_name_of_other_object,
            "scripts": [],
            "variables": [{ "name": variable_name, "value": 0, "isPersistent": False }]
        }]
        first_script_data = [0, 0, [["whenGreenFlag"],
            ["wait:elapsed:from:", 2],
            ["setVar:to:", "result", ["getAttribute:of:", variable_name, sprite_name_of_other_object]]
        ]]
        self.root_info["children"][0]["scripts"] = [first_script_data]
        raw_project = scratch.RawProject(self.root_info)
        helper_variable_name = scratch.S2CC_GETATTRIBUTE_PREFIX + "{}_readVariable:{}".format(sprite_name_of_other_object, variable_name)
        first_script_data[2][2][2] = ["readVariable", helper_variable_name]
        expected_first_object_first_script_data = first_script_data
        expected_second_object_first_script_data = [0, 0, [["whenGreenFlag"], ["doForever", [
            ["setVar:to:", helper_variable_name, ["readVariable", variable_name]],
            ["wait:elapsed:from:", scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
        ]]]]

        # validate
        assert len(raw_project.objects) == 3
        [background_object, first_object, second_object] = raw_project.objects

        # scripts of sprite objects
        assert len(background_object.scripts) == 0
        assert len(first_object.scripts) == 1
        assert len(second_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_first_script_data)
        assert script == expected_script
        script = second_object.scripts[0]
        expected_script = scratch.Script(expected_second_object_first_script_data)
        assert script == expected_script

        # sprite variables
        global_variables = background_object._dict_object["variables"]
        second_object_variables = second_object._dict_object["variables"]
        assert len(global_variables) == 2
        assert len(first_object._dict_object["variables"]) == 0
        assert len(second_object_variables) == 1
        assert global_variables[0] == { "name": "result", "value": 1, "isPersistent": False }
        assert global_variables[1] == { "name": helper_variable_name, "value": 0, "isPersistent": False }
        assert second_object_variables[0] == { "name": variable_name, "value": 0, "isPersistent": False }

    def test_convert_background_specific_attributes_of_same_object_block(self):
        cls = self.__class__
        stage_name = "Stage"
        for attribute_name, sensor_name in [("backdrop #", "backgroundIndex"), ("backdrop name", "sceneName")]:
            first_script_data = [0, 0, [["whenGreenFlag"],
                ["wait:elapsed:from:", 2],
                ["setVar:to:", "result", ["getAttribute:of:", attribute_name, stage_name]]
            ]]
            self.root_info["scripts"] = [first_script_data]
            raw_project = scratch.RawProject(self.root_info)
            first_script_data[2][2][2] = [sensor_name]
            expected_stage_object_first_script_data = first_script_data

            # validate
            assert len(raw_project.objects) == 2
            [background_object, first_object] = raw_project.objects

            # scripts of sprite objects
            assert len(background_object.scripts) == 1
            assert len(first_object.scripts) == 0
            script = background_object.scripts[0]
            expected_script = scratch.Script(expected_stage_object_first_script_data)
            assert script == expected_script

            # sprite variables
            assert len(background_object._dict_object["variables"]) == 1
            assert len(first_object._dict_object["variables"]) == 0

    def test_convert_attribute_of_same_object_block(self):
        cls = self.__class__
        sprite_name = "Sprite1"
        for attribute_name, sensor_name in cls.ATTRIBUTE_NAME_TO_SENSOR_NAME_MAP.iteritems():
            first_script_data = [0, 0, [["whenGreenFlag"],
                ["wait:elapsed:from:", 2],
                ["setVar:to:", "result", ["getAttribute:of:", attribute_name, sprite_name]]
            ]]
            self.root_info["children"][0]["scripts"] = [first_script_data]
            raw_project = scratch.RawProject(self.root_info)
            first_script_data[2][2][2] = [sensor_name]
            expected_first_object_first_script_data = first_script_data

            # validate
            assert len(raw_project.objects) == 2
            [background_object, first_object] = raw_project.objects

            # scripts of sprite objects
            assert len(background_object.scripts) == 0
            assert len(first_object.scripts) == 1
            script = first_object.scripts[0]
            expected_script = scratch.Script(expected_first_object_first_script_data)
            assert script == expected_script

            # sprite variables
            assert len(background_object._dict_object["variables"]) == 1
            assert len(first_object._dict_object["variables"]) == 0

    def test_should_convert_attribute_with_formula_block_to_zero_placeholder(self):
        cls = self.__class__
        first_script_data = [0, 0, [["whenGreenFlag"],
            ["wait:elapsed:from:", 2],
            ["setVar:to:", "result", ["getAttribute:of:", "x position", ["+", 1, 2]]]
        ]]
        self.root_info["children"][0]["scripts"] = [first_script_data]
        raw_project = scratch.RawProject(self.root_info)
        first_script_data[2][2][2] = 0
        expected_first_object_first_script_data = first_script_data

        # validate
        assert len(raw_project.objects) == 2
        [background_object, first_object] = raw_project.objects

        # scripts of sprite objects
        assert len(background_object.scripts) == 0
        assert len(first_object.scripts) == 1
        script = first_object.scripts[0]
        expected_script = scratch.Script(expected_first_object_first_script_data)
        assert script == expected_script

        # sprite variables
        assert len(background_object._dict_object["variables"]) == 1
        assert len(first_object._dict_object["variables"]) == 0

    def test_convert_attribute_of_other_object_block(self):
        cls = self.__class__
        other_object_name = "Stage"
        for attribute_name, sensor_name in cls.ATTRIBUTE_NAME_TO_SENSOR_NAME_MAP.iteritems():
            first_script_data = [0, 0, [["whenGreenFlag"],
                ["wait:elapsed:from:", 2],
                ["setVar:to:", "result", ["getAttribute:of:", attribute_name, "_stage_"]]
            ]]
            self.root_info["children"][0]["scripts"] = [first_script_data]
            raw_project = scratch.RawProject(self.root_info)
            variable_name = scratch.S2CC_GETATTRIBUTE_PREFIX + "{}_{}".format(other_object_name, sensor_name)
            expected_background_object_first_script_data = [0, 0, [['whenGreenFlag'],
                ['doForever', [
                    ["setVar:to:", variable_name, [sensor_name]],
                    ["wait:elapsed:from:", scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
                ]]
            ]]
            first_script_data[2][2][2] = ["readVariable", variable_name]
            expected_first_object_first_script_data = first_script_data

            # validate
            assert len(raw_project.objects) == 2
            [background_object, first_object] = raw_project.objects

            # scripts of sprite objects
            assert len(background_object.scripts) == 1
            assert len(first_object.scripts) == 1
            script = background_object.scripts[0]
            expected_script = scratch.Script(expected_background_object_first_script_data)
            assert script == expected_script
            script = first_object.scripts[0]
            expected_script = scratch.Script(expected_first_object_first_script_data)
            assert script == expected_script

            # sprite variables
            stage_object_variables = background_object._dict_object["variables"]
            assert len(stage_object_variables) == 2
            assert len(first_object._dict_object["variables"]) == 0
            assert stage_object_variables[0] == { "name": "result", "value": 1, "isPersistent": False }
            assert stage_object_variables[1] == { "name": variable_name, "value": 0, "isPersistent": False }

    def test_convert_attribute_of_other_object_block_encapsulated(self):
        cls = self.__class__
        other_object_name = "Stage"
        for attribute_name, sensor_name in cls.ATTRIBUTE_NAME_TO_SENSOR_NAME_MAP.iteritems():
            first_script_data = [0, 0, [["whenGreenFlag"],
                ["wait:elapsed:from:", 2],
                ["doRepeat", 10,
                    [["doIf", False, [["doIfElse", False,
                        [["doForever",
                            [["setVar:to:", "result", ["getAttribute:of:", attribute_name, "_stage_"]]]
                        ]], 0]]]
                ]]
            ]]
            self.root_info["children"][0]["scripts"] = [first_script_data]
            raw_project = scratch.RawProject(self.root_info)
            variable_name = scratch.S2CC_GETATTRIBUTE_PREFIX + "{}_{}".format(other_object_name, sensor_name)
            expected_background_object_first_script_data = [0, 0, [['whenGreenFlag'],
                ['doForever', [
                    ["setVar:to:", variable_name, [sensor_name]],
                    ["wait:elapsed:from:", scratch.UPDATE_HELPER_VARIABLE_TIMEOUT]
                ]]
            ]]
            first_script_data[2][2][2][0][2][0][2][0][1][0][2] = ["readVariable", variable_name]
            expected_first_object_first_script_data = first_script_data

            # validate
            assert len(raw_project.objects) == 2
            [background_object, first_object] = raw_project.objects

            # scripts of sprite objects
            assert len(background_object.scripts) == 1
            assert len(first_object.scripts) == 1
            script = background_object.scripts[0]
            expected_script = scratch.Script(expected_background_object_first_script_data)
            assert script == expected_script
            script = first_object.scripts[0]
            expected_script = scratch.Script(expected_first_object_first_script_data)
            assert script == expected_script

            # sprite variables
            stage_object_variables = background_object._dict_object["variables"]
            assert len(stage_object_variables) == 2
            assert len(first_object._dict_object["variables"]) == 0
            assert stage_object_variables[0] == { "name": "result", "value": 1, "isPersistent": False }
            assert stage_object_variables[1] == { "name": variable_name, "value": 0, "isPersistent": False }


class CommentWorkaround(unittest.TestCase):
    COMMENT_DATA_TEMPLATE = {
        "objName": "Stage",
        "sounds": [],
        "costumes": [],
        "currentCostumeIndex": 0,
        "penLayerMD5": "5c81a336fab8be57adc039a8a2b33ca9.png",
        "penLayerID": 0,
        "tempoBPM": 60,
        "videoAlpha": 0.5,
        "children": [],
        "info": {}
    }

    def get_stage(self, scripts, comments):
        data = self.COMMENT_DATA_TEMPLATE
        data["scriptComments"] = comments
        data["scripts"] = scripts
        raw_project = scratch.RawProject(data)
        self.assertEqual(1, len(raw_project.objects))
        return raw_project.objects[0]

    @classmethod
    def get_comment(cls, blockId, text):
        return [0, 0, 0, 0, False, blockId, text]

    def test_simple_comment(self):
        for blockId in [-1, 0, 1]:
            script = [0, 0, [["whenGreenFlag"], ["wait:elapsed:from:", 1]]]
            comment = self.get_comment(1, "test_comment")
            stage = self.get_stage([script], [comment])

            self.assertEqual(1, len(stage.scripts))
            script = stage.scripts[0]
            self.assertListEqual([['note:', 'test_comment'], ['wait:elapsed:from:', 1]], script.blocks)

    def test_condition_comment(self):
        script = [0, 0, [["whenGreenFlag"], ["wait:elapsed:from:", 1], ["wait:elapsed:from:", ["+", 1, 2]], ["wait:elapsed:from:", 1]]]
        comments = [self.get_comment(3, "condition_comment"), self.get_comment(4, "wait_comment")]
        stage = self.get_stage([script], comments)

        self.assertEqual(1, len(stage.scripts))
        script = stage.scripts[0]
        expected_blocks = [['wait:elapsed:from:', 1],
                           ['note:', 'condition_comment'],
                           ['wait:elapsed:from:', ['+', 1, 2]],
                           ['note:', 'wait_comment'],
                           ['wait:elapsed:from:', 1]]
        self.assertListEqual(expected_blocks, script.blocks)

    def test_comment_in_if(self):
        script = [0, 0, [["whenGreenFlag"], ["doIf", [">", 5, 4], [["wait:elapsed:from:", 1]]], ["wait:elapsed:from:", 1]]]
        comments = [self.get_comment(3, "in_if_comment"), self.get_comment(4, "after_if_comment")]
        stage = self.get_stage([script], comments)

        self.assertEqual(1, len(stage.scripts))
        script = stage.scripts[0]
        expected_blocks = [['doIf',
                            ['>', 5, 4],
                            [['note:', 'in_if_comment'], ['wait:elapsed:from:', 1]]],
                           ['note:', 'after_if_comment'],
                           ['wait:elapsed:from:', 1]]
        self.assertListEqual(expected_blocks, script.blocks)

    def test_comment_in_else(self):
        script = [0, 0, [["whenGreenFlag"], ["doIfElse", [">", 5, 4], [["wait:elapsed:from:", 1]], [["wait:elapsed:from:", 2]]], ["wait:elapsed:from:", 1]]]
        comments = [self.get_comment(3, "in_if_comment"), self.get_comment(4, "in_else_comment"), self.get_comment(5, "after_if_comment")]
        stage = self.get_stage([script], comments)

        self.assertEqual(1, len(stage.scripts))
        script = stage.scripts[0]
        expected_blocks = [['doIfElse',
                            ['>', 5, 4],
                            [['note:', 'in_if_comment'], ['wait:elapsed:from:', 1]],
                            [['note:', 'in_else_comment'], ['wait:elapsed:from:', 2]]],
                           ['note:', 'after_if_comment'],
                           ['wait:elapsed:from:', 1]]
        self.assertListEqual(expected_blocks, script.blocks)

    def test_multiple_comments_same_brick(self):
        NUM_COMMENTS = 20
        for blockId in [-1, 0, 1, 2]:
            script = [0, 0, [["whenGreenFlag"], ["wait:elapsed:from:", ["+", 1, 2]]]]
            comments = [self.get_comment(1, "test_comment_{}".format(i)) for i in range(NUM_COMMENTS)]
            stage = self.get_stage([script], comments)

            self.assertEqual(1, len(stage.scripts))
            script = stage.scripts[0]
            expected_blocks = [["note:", "test_comment_{}".format(i)] for i in range(NUM_COMMENTS)][::-1] + [["wait:elapsed:from:", ["+", 1, 2]]]
            self.assertListEqual(expected_blocks, script.blocks)

    def test_invalid_blocks(self):
        scripts = [
            [0, 0, [["whenGreenFlag"], ["wait:elapsed:from:", ["+", 1, 2]]]],
            [0, 0, [["+", 4, 3]]],
            [0, 0, [["wait:elapsed:from:", "-", 2, -1]]],
            [0, 0, [["whenGreenFlag"], ["wait:elapsed:from:", ["+", 1, 2]]]]
        ]
        comments = [self.get_comment(i, "comment_{}".format(i)) for i in range(8)]
        stage = self.get_stage(scripts, comments)

        self.assertEqual(2, len(stage.scripts))
        expected_blocks_0 = [['note:', 'comment_0'],
                             ['note:', 'comment_1'],
                             ['note:', 'comment_2'],
                             ['wait:elapsed:from:', ['+', 1, 2]]]
        self.assertListEqual(expected_blocks_0, stage.scripts[0].blocks)
        expected_blocks_1 = [['note:', 'comment_5'],
                             ['note:', 'comment_6'],
                             ['note:', 'comment_7'],
                             ['wait:elapsed:from:', ['+', 1, 2]]]
        self.assertListEqual(expected_blocks_1, stage.scripts[1].blocks)

    def test_general_comment_without_scripts(self):
        comment = self.get_comment(-1, "general comment")
        stage = self.get_stage([], [comment])
        self.assertListEqual([], stage.scripts)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
