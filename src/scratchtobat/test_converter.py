from java.lang import System
from scratchtobat import converter, sb2, common, common_testing
import glob
import org.catrobat.catroid.common as catcommon
import org.catrobat.catroid.content as catbase
import org.catrobat.catroid.content.bricks as catbricks
import org.catrobat.catroid.formulaeditor as catformula
import os
import shutil
import tempfile
import unittest


DUMMY_CATR_SPRITE = catbase.Sprite("Dummy")
TEST_PROJECT_PATH = common_testing.get_test_project_path("dancing_castle")


class TestConvertExampleProject(common_testing.ScratchtobatTestCase):
    
    dummy_sb2_object = sb2.Object({"objName" : "Dummy"})
    
    expected_sprite_names = ["Sprite1, Cassy Dance"]
    expected_script_classes = [[catbase.StartScript, ], []]
    expected_brick_classes = [[catbricks.WaitBrick, catbricks.RepeatBrick, catbricks.MoveNStepsBrick, catbricks.WaitBrick, catbricks.MoveNStepsBrick,
            catbricks.WaitBrick, catbricks.LoopEndBrick], []]
    
    def __init__(self, methodName='runTest'):
        common_testing.ScratchtobatTestCase.__init__(self, methodName=methodName)
        assert System.getProperty("python.security.respectJavaAccessibility") == 'false', "Jython registry property 'python.security.respectJavaAccessibility' must be set to 'false'"
    
    def setUp(self):
        common_testing.ScratchtobatTestCase.setUp(self)
        self.project_parent = sb2.Project(TEST_PROJECT_PATH)
        self.project = self.project_parent.project_code
        self.temp_dir = tempfile.mkdtemp()
    
    def test_can_convert_to_catroid_folder_structure_with_svg_to_png(self):
        count_svg_and_png_files = 0 
        for md5_name in self.project_parent.md5_to_resource_path_map:
            common.log.info(md5_name)
            if os.path.splitext(md5_name)[1] in {".png", ".svg"}:
                count_svg_and_png_files += 1
                
        converter.convert_sb2_project_to_catroid_project_structure(self.project_parent, self.temp_dir)
        
        images_dir = converter.images_path_of_project(self.temp_dir)
        self.assertTrue(os.path.exists(images_dir))
        self.assertTrue(os.listdir(images_dir))
        sounds_dir = converter.sounds_path_of_project(self.temp_dir)
        self.assertTrue(os.path.exists(sounds_dir))
        self.assertTrue(os.listdir(sounds_dir))
        code_xml_path = os.path.join(self.temp_dir, converter.CATROID_PROJECT_FILE)
        self.assertTrue(os.path.exists(code_xml_path))
        self.assertFalse(glob.glob(os.path.join(images_dir, "*.svg")), "Unsupported svg files are in catroid folder.")
        actual_count = len(glob.glob(os.path.join(images_dir, "*.png")))
        # TODO: + 1 because of missing penLayerMD5 file
        self.assertEqual(count_svg_and_png_files, actual_count + 1)
        
        self.assertCorrectCatroidProjectStructure(self.temp_dir, self.project_parent.name)
    
#     def test_can_convert_to_catroid_folder_structure_with_utf_input_json(self):
#         project = sb2.Project(common_testing.get_test_project_path("simple_utf_test"))
#         converter.convert_sb2_project_to_catroid_project_structure(project, self.temp_dir)
#         
#         self.assertCorrectCatroidProjectStructure(self.temp_dir, project.name)
    
    def test_can_get_catroid_resource_file_name_of_sb2_resources(self):
        resource_names_sb2_to_catroid_map = {
            "83a9787d4cb6f3b7632b4ddfebf74367.wav": "83a9787d4cb6f3b7632b4ddfebf74367_pop.wav",
            "510da64cf172d53750dffd23fbf73563.png": "510da64cf172d53750dffd23fbf73563_backdrop1.png",
            "033f926829a446a28970f59302b0572d.png":"033f926829a446a28970f59302b0572d_castle1.png",
            "83c36d806dc92327b9e7049a565c6bff.wav":"83c36d806dc92327b9e7049a565c6bff_meow.wav"}
        for resource_name in resource_names_sb2_to_catroid_map:
            expected = resource_names_sb2_to_catroid_map[resource_name]
            self.assertEqual(expected, converter.catroid_resource_name_of_sb2_resource(self.project_parent, resource_name))

    def test_can_convert_sb2_project_to_catroid_zip(self):        
#         self.addCleanup(lambda: shutil.rmtree(temp_dir))
        catroid_zip_file_name = os.path.join(self.temp_dir, "project.catroid") 
        
        converter.convert_sb2_project_to_catroid_zip(self.project_parent, catroid_zip_file_name) 
        
        self.assertCorrectZipFile(catroid_zip_file_name, self.project_parent.name)
    
#     def test_can_convert_sb2_project_with_utf_to_catroid_zip(self):        
# #         self.addCleanup(lambda: shutil.rmtree(temp_dir))
#         catroid_zip_file_name = os.path.join(self.temp_dir, "project.catroid") 
#         project = sb2.Project(common_testing.get_test_project_path("simple_utf_test"))
#         converter.convert_sb2_project_to_catroid_zip(project, catroid_zip_file_name) 
#         
#         self.assertCorrectZipFile(catroid_zip_file_name, project.name)
        
    def test_can_convert_complete_project_to_catrobat_project_class(self):
        catr_project = converter.convert_to_catrobat_project(self.project_parent)
        self.assertTrue(isinstance(catr_project, catbase.Project), "Converted project is not a catroid project class.")
        
        self.assertEqual(360, catr_project.getXmlHeader().virtualScreenHeight, "Project height not at Scratch stage size")
        self.assertEqual(480, catr_project.getXmlHeader().virtualScreenWidth, "Project width not at Scratch stage size")
        
        catr_sprites = catr_project.getSpriteList()
        self.assertTrue(catr_sprites, "No sprites in converted project.")
        self.assertTrue(all(isinstance(_, catbase.Sprite) for _ in catr_sprites), "Sprites of converted project are not catroid sprite classes.")
        
    def test_can_convert_object_to_catrobat_sprite_class(self):
        sprites = [converter._convert_to_catrobat_sprite(sb2obj) for sb2obj in self.project.objects]
        self.assertTrue(all(isinstance(_, catbase.Sprite) for _ in sprites))
        
        sprite_0 = sprites[0] 
        self.assertEqual("Stage", sprite_0.getName())
        self.assertEqual([catbase.StartScript], [_.__class__ for _ in sprite_0.scriptList])
        start_script = sprite_0.scriptList[0]
        # TODO into own test case
        set_look_brick = start_script.getBrick(0)
        self.assertTrue(isinstance(set_look_brick, catbricks.SetLookBrick), "Mismatch to Scratch behavior: Implicit SetLookBrick is missing")
         
        sprite0_looks = sprite_0.getLookDataList()
        self.assertTrue(sprite0_looks, "No looks in sprite1")
        self.assertTrue(all(isinstance(_, catcommon.LookData) for _ in sprite0_looks), "Wrong classes in look list1")
        sprite0_sounds = sprite_0.getSoundList()
        self.assertTrue(sprite0_sounds, "No sounds in sprite1")
        self.assertTrue(all(isinstance(_, catcommon.SoundInfo) for _ in sprite0_sounds), "Wrong classes in sound list1")
        
        sprite_1 = sprites[1]
        self.assertEqual("Sprite1", sprite_1.getName())
        self.assertEqual([catbase.StartScript, catbase.BroadcastScript], [_.__class__ for _ in sprite_1.scriptList])
        
        start_script = sprite_1.scriptList[0]
        # TODO into own test case
        place_at_brick = start_script.getBrick(1)
        self.assertTrue(isinstance(place_at_brick, catbricks.PlaceAtBrick), "Mismatch to Scratch behavior: Implicit PlaceAtBrick is missing")
        self.assertEqual(place_at_brick.xPosition.formulaTree.type, catformula.FormulaElement.ElementType.NUMBER)
        self.assertEqual(place_at_brick.xPosition.formulaTree.value, str(self.project.objects[1].get_scratchX()))
        self.assertEqual(place_at_brick.yPosition.formulaTree.type, catformula.FormulaElement.ElementType.NUMBER)
        self.assertEqual(place_at_brick.yPosition.formulaTree.value, str(self.project.objects[1].get_scratchY())) 
        
        sprite1_looks = sprite_1.getLookDataList()
        self.assertTrue(sprite1_looks, "No looks in sprite1")
        self.assertTrue(all(isinstance(_, catcommon.LookData) for _ in sprite1_looks), "Wrong classes in look list1")
        sprite1_sounds = sprite_1.getSoundList()
        self.assertTrue(sprite1_sounds, "No sounds in sprite1")
        self.assertTrue(all(isinstance(_, catcommon.SoundInfo) for _ in sprite1_sounds), "Wrong classes in sound list1")
        
        sprite_2 = sprites[2]
        self.assertEqual("Cassy Dance", sprite_2.getName())
        self.assertEqual([catbase.StartScript], [_.__class__ for _ in sprite_2.scriptList])
        sprite2_looks = sprite_2.getLookDataList()
        self.assertTrue(sprite2_looks, "No looks in sprite2")
        self.assertTrue(all(isinstance(_, catcommon.LookData) for _ in sprite2_looks), "Wrong classes in look list2")

    def test_can_convert_script_to_catrobat_script_class(self):
        sb2_script = self.project.objects[1].scripts[0]
        catr_script = converter._convert_to_catrobat_script(sb2_script, DUMMY_CATR_SPRITE)
        self.assertTrue(catr_script, "No script from conversion")
        expected_script_class = [catbase.StartScript]
        expected_brick_classes = [catbricks.WaitBrick, catbricks.RepeatBrick, catbricks.MoveNStepsBrick, catbricks.WaitBrick, catbricks.MoveNStepsBrick,
            catbricks.WaitBrick, catbricks.LoopEndBrick]
        self.assertScriptClasses(expected_script_class, expected_brick_classes, catr_script)
    
    def test_can_convert_costume_to_catrobat_lookdata_class(self):
        costumes = self.project.objects[1].get_costumes()
        for expected_values, costume in zip([("costume1", "f9a1c175dbe2e5dee472858dd30d16bb_costume1.svg"),
                ("costume2", "6e8bd9ae68fdb02b7e1e3df656a75635_costume2.svg")], costumes):
            look = converter._convert_to_catrobat_look(costume) 
            self.assertTrue(isinstance(look, catcommon.LookData), "Costume conversion return wrong class")
            self.assertEqual(look.getLookName(), expected_values[0], "Look name wrong")
            self.assertEqual(look.getLookFileName(), expected_values[1], "Look file name wrong")
        
    def test_can_convert_sound_to_catrobat_soundinfo_class(self):
        sounds = self.project.objects[1].get_sounds()
        for expected_values, sound in zip([("meow", "83c36d806dc92327b9e7049a565c6bff_meow.wav"), ], sounds):
            soundinfo = converter._convert_to_catrobat_sound(sound) 
            self.assertTrue(isinstance(soundinfo, catcommon.SoundInfo), "Sound conversion return wrong class")
            self.assertEqual(soundinfo.getTitle(), expected_values[0], "Sound name wrong")
            self.assertEqual(soundinfo.getSoundFileName(), expected_values[1], "Sound file name wrong")
    
    def test_can_write_sb2_project_to_catrobat_xml(self):
        catr_project = converter.convert_to_catrobat_project(self.project_parent)
#         common.log.info(catio.StorageHandler.getInstance().getXMLStringOfAProject(catr_project))
        
    def tearDown(self):
        common_testing.ScratchtobatTestCase.tearDown(self)
        # FIXME: jython / windows workaround.. reason?
        
        shutil.rmtree(self.temp_dir)
        

class TestConvertBricks(unittest.TestCase):
    
    def get_sprite_with_soundinfo(self, soundinfo_name):
        dummy_sound = catcommon.SoundInfo()
        dummy_sound.setTitle(soundinfo_name)
        dummy_sprite = catbase.Sprite("TestDummy")
        dummy_sprite.getSoundList().add(dummy_sound)
        return dummy_sprite
    
    def test_fail_on_unknown_brick(self):
        with self.assertRaises(common.ScratchtobatError):
            converter._convert_to_catrobat_bricks(['wrong_brick_name_zzz', 10, 10], DUMMY_CATR_SPRITE)
    
    def test_can_convert_loop_bricks(self):
        sb2_do_loop = ["doRepeat", 10, [[u'forward:', 10], [u'playDrum', 1, 0.2], [u'forward:', -10], [u'playDrum', 1, 0.2]]]
        catr_do_loop = converter._convert_to_catrobat_bricks(sb2_do_loop, DUMMY_CATR_SPRITE)
        self.assertTrue(isinstance(catr_do_loop, list))
        # 1 loop start + 4 inner loop bricks + 1 loop end = 6
        self.assertEqual(6, len(catr_do_loop))
        expected_brick_classes = [catbricks.RepeatBrick, catbricks.MoveNStepsBrick, catbricks.WaitBrick, catbricks.MoveNStepsBrick,
            catbricks.WaitBrick, catbricks.LoopEndBrick]
        self.assertEqual(expected_brick_classes, [_.__class__ for _ in catr_do_loop])

    def test_can_convert_waitelapsedfrom_brick(self):
        sb2_brick = ["wait:elapsed:from:", 1]
        [catr_brick] = converter._convert_to_catrobat_bricks(sb2_brick, DUMMY_CATR_SPRITE)
        self.assertTrue(isinstance(catr_brick, catbricks.WaitBrick))
        formula_seconds = catr_brick.timeToWaitInSeconds.formulaTree
        self.assertEqual(formula_seconds.type, catformula.FormulaElement.ElementType.NUMBER)
        self.assertEqual(formula_seconds.value, "1.0")

    def test_fail_convert_playsound_brick_if_sound_missing(self):
        sb2_brick = ["playSound:", "bird"]
        with self.assertRaises(converter.ConversionError):
            converter._convert_to_catrobat_bricks(sb2_brick, DUMMY_CATR_SPRITE)
    
    def test_can_convert_playsound_brick(self):
        sb2_brick = ["playSound:", "bird"]
        dummy_sprite = self.get_sprite_with_soundinfo(sb2_brick[1])
        [catr_brick] = converter._convert_to_catrobat_bricks(sb2_brick, dummy_sprite)
        self.assertTrue(isinstance(catr_brick, catbricks.PlaySoundBrick))
        self.assertEqual(sb2_brick[1], catr_brick.sound.getTitle())
        
    def test_can_convert_nextcostume_brick(self):
        sb2_brick = ["nextCostume"]
        [catr_brick] = converter._convert_to_catrobat_bricks(sb2_brick, DUMMY_CATR_SPRITE)
        self.assertTrue(isinstance(catr_brick, catbricks.NextLookBrick))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
