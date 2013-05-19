from scratchtobat import sb2, testing_common
import unittest
import os

EASY_SCRIPTS = [[23, 125,
        [["whenGreenFlag"],
            ["say:duration:elapsed:from:", "Watch me dance!", 2],
            ["doRepeat",
                10,
                [["forward:", 10],
                    ["playDrum", 1, 0.2],
                    ["forward:", -10],
                    ["playDrum", 1, 0.2]]]]],
    [30, 355, [["whenKeyPressed", "space"], ["changeGraphicEffect:by:", "color", 25]]]]


class TestProjectInit(unittest.TestCase):
    def test_can_create_reader_from_correct_json_file(self):
        scratch_reader = sb2.Project(testing_common.get_test_project_path("simple"))
        self.assertTrue(scratch_reader, "No reader object")

    def test_fail_on_wrong_input_path(self):
        with self.assertRaises(sb2.ProjectError):
            # TODO: check error type
            sb2.Project(testing_common.get_test_project_path("non_existing_path"))
        
    def test_can_detect_corrupt_sb2_json_file(self):
        with self.assertRaises(sb2.ProjectError):
            # TODO: check error type
            sb2.Project(testing_common.get_test_project_path("wrong"))


class TestProjectFunc(unittest.TestCase):
    def setUp(self):
        self.scratch_reader = sb2.Project(testing_common.get_test_project_path("simple"))

    def test_can_read_sb2_json(self):
        json_dict = self.scratch_reader.get_raw_data()
        self.assertEquals(json_dict["objName"], "Stage")
        self.assertTrue(json_dict["info"])


# class TestCanCreateSb2ObjectInstance(unittest.TestCase):
#      
#     def testCanCreateSingleOnCorrectInput(self):
#         self.fail("Not implemented")


class TestScriptInit(unittest.TestCase):

    def testCanCreateSingleOnCorrectInput(self):
        for script_input in EASY_SCRIPTS: 
            script = sb2.Script(script_input)
            self.assertTrue(script)

    def testFailOnWrongInput(self):
        faulty_script_structures = [[],
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
        
    def test_can_access_bricks(self):
        self.assertEqual(['whenGreenFlag', 'say:duration:elapsed:from:', 'doRepeat', 'forward:', 'playDrum', 'forward:', 'playDrum'], self.script.get_bricks())


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
