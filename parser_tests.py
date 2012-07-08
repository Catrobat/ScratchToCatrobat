import unittest
import os
import xml.dom.minidom
from parser import ScratchOutputParser

class TestScratchOutputParser(unittest.TestCase):
    def setUp(self):
        self.project_folder = "test_scratch_output/"
        self.sprite_name = "SpriteName"
        self.parser = ScratchOutputParser(self.project_folder, "ProjectName")
        self.parser.process_project()

    def test_aparser(self):
        self.assertEquals(len(self.parser.sprites), 1)
        self.assertEquals(self.parser.sprites[0][0], self.sprite_name)
        bricks_params = self.parser.sprites[0][1]

        self.assertEquals(len(bricks_params), 11)
        self.assertEquals(bricks_params[0], ("Bricks.MoveNStepsBrick", {"steps": "10"}))
        self.assertEquals(bricks_params[1], ("Bricks.TurnRightBrick", {"degrees": "15"}))
        self.assertEquals(bricks_params[2], ("Bricks.TurnLeftBrick", {"degrees": "15"}))
        self.assertEquals(bricks_params[3], ("Bricks.PointInDirectionBrick", {"degrees": "90"}))
        self.assertEquals(bricks_params[4], ("Bricks.PlaceAtBrick", {"xPosition": "0", "yPosition": "-100"}))
        self.assertEquals(bricks_params[5], ("Bricks.GlideToBrick", {"xDestination": "0", "durationInMilliSeconds": "1000", "yDestination": "-100"}))
        self.assertEquals(bricks_params[6], ("Bricks.ChangeXByBrick", {"xMovement": "10"}))
        self.assertEquals(bricks_params[7], ("Bricks.SetXBrick", {"xPosition": "0"}))
        self.assertEquals(bricks_params[8], ("Bricks.ChangeYByBrick", {"yMovement": "10"}))
        self.assertEquals(bricks_params[9], ("Bricks.SetYBrick", {"yPosition": "0"}))
        self.assertEquals(bricks_params[10], ("Bricks.IfOnEdgeBounceBrick", {}))

    def test_media_files(self):
        costume_name = "costumeName"
        sound_filename = "soundName.wav"
        costumes = os.listdir(os.path.join(self.parser.temp_folder, 'images'))
        sounds = os.listdir(os.path.join(self.parser.temp_folder, 'sounds'))
        costumes = filter(lambda x: not x.startswith('.'), costumes)
        sounds = filter(lambda x: not x.startswith('.'), sounds)

        self.assertEquals(len(costumes), 1)
        self.assertEquals(len(sounds), 1)

        self.assertTrue(costumes[0].endswith(self.sprite_name + '_' + costume_name + '.png'))
        self.assertTrue(sounds[0].endswith(self.sprite_name + '_' + sound_filename))