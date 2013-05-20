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
    
    def __init__(self, methodName='runTest', project_name='dancing_castle'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.project_name = project_name
        
    def setUp(self):
        self.project = sb2.Project(testing_common.get_test_project_path(self.project_name))

    def test_can_read_sb2_json(self):
        json_dict = self.project.get_raw_data()
        self.assertEquals(json_dict["objName"], "Stage")
        self.assertTrue(json_dict["info"])

    def test_can_access_project_name(self):
        self.assertEqual(self.project_name, self.project.name)
        
    def test_can_access_sb2_objects(self):
        for sb2_object in self.project.objects:
            self.assertTrue(sb2_object)
            self.assertTrue(isinstance(sb2_object, sb2.Object))


class TestObjectInit(TestProjectFunc):
      
    def test_can_on_correct_input(self):
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


class TestObjectFunc(TestProjectFunc):
    
    def __init__(self, methodName='runTest', project_name='dancing_castle'):
        TestProjectFunc.__init__(self, methodName=methodName, project_name=project_name)
    
    def setUp(self):
        TestProjectFunc.setUp(self)
        self.sb2_objects = self.project.objects
    
    def test_fail_on_wrong_data_access_key(self):
        with self.assertRaises(AttributeError):
            self.sb2_objects[0].get_wrongkey()
        
    def test_can_access_scripts(self):
        self.assertEquals(['Sprite1', 'Cassy Dance'], [_.get_objName() for _ in self.sb2_objects])
        for sb2_object in self.sb2_objects:
            self.assertTrue(len(sb2_object.scripts) > 0)
            for sb2_script in sb2_object.scripts:
                self.assertTrue(sb2_script)
                self.assertTrue(isinstance(sb2_script, sb2.Script))
            

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

    def test_can_read_sb2_script_data(self):
        self.assertEqual('whenGreenFlag', self.script.get_type())
        expected_brick_names = ['say:duration:elapsed:from:', 'doRepeat', 'forward:', 'playDrum', 'forward:', 'playDrum']
        self.assertEqual(expected_brick_names, self.script.get_raw_bricks())
        

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
