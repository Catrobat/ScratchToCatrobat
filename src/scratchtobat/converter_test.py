from __future__ import unicode_literals

import unittest
import org.catrobat.catroid.content as catbase
import org.catrobat.catroid.content.bricks as catbricks
import org.catrobat.catroid.io as catio
from scratchtobat import sb2_test, converter, sb2, common


class TestConverter(sb2_test.TestProjectFunc):
    
    dummy_sb2_object = sb2.Object({"objName" : "Dummy"})
    dummy_catr_sprite = catbase.Sprite("Dummy")
    
    def __init__(self, methodName='runTest', project_name='dancing_castle'):
        sb2_test.TestProjectFunc.__init__(self, methodName=methodName, project_name=project_name)

    def test_can_convert_object_to_catrobat_sprite_class(self):
        sprites = [converter.convert_to_catrobat_sprite(sb2obj) for sb2obj in self.project.objects]
        self.assertTrue(all(isinstance(_, catbase.Sprite) for _ in sprites))
        
        self.assertEqual("Sprite1", sprites[0].getName())
        self.assertEqual(2, sprites[0].getNumberOfScripts())
        self.assertEqual(8, sprites[0].getNumberOfBricks())
        
        self.assertEqual("Cassy Dance", sprites[1].getName())
        self.assertEqual(1, sprites[1].getNumberOfScripts())
        self.assertEqual(5, sprites[1].getNumberOfBricks())
        
    def test_can_convert_script_to_catrobat_script_class(self):
        first_object = self.project.objects[0]
        first_script_of_object = self.project.objects[0].scripts[0]
        catr_script = converter.convert_to_catrobat_script(first_script_of_object, converter.convert_to_catrobat_sprite(first_object))
        self.assertEqual(catbase.StartScript, catr_script.__class__)

    def test_can_convert_bricks_to_catrobat_brick_class(self):
        first_object = self.project.objects[0]
        first_script_of_object = self.project.objects[0].scripts[0]
        catr_script = converter.convert_to_catrobat_script(first_script_of_object, converter.convert_to_catrobat_sprite(first_object))
        self.assertEqual(["say:duration:elapsed:from:", "doRepeat"], [_[0] for _ in first_script_of_object.script_bricks])
        bricks = catr_script.getBrickList()
        self.assertEqual(7, len(bricks))
        expected_brick_classes = [catbricks.WaitBrick, catbricks.RepeatBrick, catbricks.MoveNStepsBrick, catbricks.WaitBrick, catbricks.MoveNStepsBrick,
            catbricks.WaitBrick, catbricks.LoopEndBrick]
        self.assertEqual(expected_brick_classes, [_.__class__ for _ in bricks])

    def test_can_convert_loop_bricks(self):
        sb2_do_loop = ["doRepeat", 10, [[u'forward:', 10], [u'playDrum', 1, 0.2], [u'forward:', -10], [u'playDrum', 1, 0.2]]]
        catr_do_loop = converter.convert_to_catrobat_bricks(sb2_do_loop, self.dummy_catr_sprite)
        self.assertTrue(isinstance(catr_do_loop, list))
        # 1 loop start + 4 inner loop bricks + 1 loop end = 6
        self.assertEqual(6, len(catr_do_loop))
        expected_brick_classes = [catbricks.RepeatBrick, catbricks.MoveNStepsBrick, catbricks.WaitBrick, catbricks.MoveNStepsBrick,
            catbricks.WaitBrick, catbricks.LoopEndBrick] 
        self.assertEqual(expected_brick_classes, [_.__class__ for _ in catr_do_loop])
        
    def test_can_convert_project_to_catrobat_project_class(self):
        catr_project = converter.convert_to_catrobat_project(self.project)
        self.assertTrue(isinstance(catr_project, catbase.Project))
        self.assertTrue(all(isinstance(_, catbase.Sprite) for _ in catr_project.getSpriteList()))
        self.assertEqual(2, len(catr_project.getSpriteList()))
        self.assertEqual(["Sprite1", "Cassy Dance"], [_.getName() for _ in catr_project.getSpriteList()])
        
    def test_can_write_sb2_project_to_catrobat_xml(self):
        catr_project = converter.convert_to_catrobat_project(self.project)
        common.log.info(catio.StorageHandler.getInstance().getXMLStringOfAProject(catr_project))        

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
