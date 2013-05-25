from scratchtobat import sb2, testing_common
import unittest


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


TEST_PROJECT_NAME = "dancing_castle"


class TestProjectInit(unittest.TestCase):
    def test_can_construct_on_correct_input(self):
        project = sb2.Project(testing_common.get_test_project_path("simple"))
        self.assertTrue(project, "No project object")

    def test_fail_on_non_existing_input_path(self):
        with self.assertRaises(sb2.ProjectError):
            # TODO: check error type
            sb2.Project(testing_common.get_test_project_path("non_existing_path"))
        
    def test_fail_on_corrupt_sb2_json_input(self):
        with self.assertRaises(sb2.ProjectError):
            # TODO: check error type
            sb2.Project(testing_common.get_test_project_path("wrong"))


class TestProjectFunc(unittest.TestCase):
    
    def __init__(self, methodName='runTest', project_name='dancing_castle'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.project_name = project_name
        
    def setUp(self):
        self.project = sb2.Project(testing_common.get_test_project_path(self.project_name))

    def test_can_access_input_data(self):
        json_dict = self.project.get_raw_data()
        self.assertEquals(json_dict["objName"], "Stage")
        self.assertTrue(json_dict["info"])

    def test_can_access_project_name(self):
        self.assertEqual(self.project_name, self.project.name)
        
    def test_can_access_sb2_objects(self):
        for sb2_object in self.project.objects:
            self.assertTrue(sb2_object)
            self.assertTrue(isinstance(sb2_object, sb2.Object))
        self.assertEqual("Stage", self.project.objects[0].get_objName(), "Stage object missing")
        self.assertEqual(['Stage', 'Sprite1', 'Cassy Dance'], [_.get_objName() for _ in self.project.objects])


class TestObjectInit(unittest.TestCase):
      
    def setUp(self):
        self.project = sb2.Project(testing_common.get_test_project_path(TEST_PROJECT_NAME))
        
    def test_can_construct_on_correct_input(self):
        for obj_data in self.project.objects_data:
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
        self.project = sb2.Project(testing_common.get_test_project_path(TEST_PROJECT_NAME))
        self.sb2_objects = self.project.objects
    
    def test_can_call_for_wrong_key_like_regular_dict_get(self):
        self.assertEqual(None, self.sb2_objects[0].get_wrongkey())
        
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


class TestScriptInit(unittest.TestCase):

    def test_can_construct_on_correct_input(self):
        for script_input in EASY_SCRIPTS: 
            script = sb2.Script(script_input)
            self.assertTrue(script)

    def test_fail_on_wrong_input(self):
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

    def test_can_access_sb2_script_data(self):
        self.assertEqual('whenGreenFlag', self.script.get_type())
        expected_brick_names = ['say:duration:elapsed:from:', 'doRepeat', 'forward:', 'playDrum', 'forward:', 'playDrum']
        self.assertEqual(expected_brick_names, self.script.get_raw_bricks())
        
        
if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
