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
import imghdr
import os
import re
import shutil
import unittest
from threading import Lock

from scratchtocatrobat.tools import common_testing
from scratchtocatrobat.tools import svgtopng
from scratchtocatrobat.tools import helpers

import xml.etree.cElementTree as ET

ns_registry_lock = Lock()

class SvgToPngTest(common_testing.BaseTestCase):

    #def test_can_convert_file_from_svg_to_png(self):
    #    regular_svg_path = os.path.join(common_testing.get_test_project_path("dancing_castle"), "1.svg")
    #    svg_path_with_fileext = os.path.join(self.temp_dir, "test_path_which_includes_extension_.svg.svg", "1.svg")
    #    os.makedirs(os.path.dirname(svg_path_with_fileext))
    #    shutil.copy(regular_svg_path, svg_path_with_fileext)
    #    for input_svg_path in [regular_svg_path, svg_path_with_fileext]:
    #        assert os.path.exists(input_svg_path)
    #       output_png_path = svgtopng.convert(input_svg_path)
    #        assert os.path.exists(output_png_path) 
    #        assert imghdr.what(output_png_path) == "png"
                
    def test_parse_svgfile_and_convert_to_png_cape(self):
        img_proc_dir = os.path.join(helpers.APP_PATH, "test", "res", "img_proc_png")
        input_svg_path = os.path.join(img_proc_dir, "input_cape.svg")
        expected_image_path = os.path.join(img_proc_dir, "expected_cape.png")
        
        assert os.path.exists(input_svg_path)
        
        rotation_x, rotation_y = 36, 67
        
        output_png_path = svgtopng.convert(input_svg_path, rotation_x, rotation_y, ns_registry_lock)
        
        from javax.imageio import ImageIO
        from java.io import File
        bufferd_image = ImageIO.read(File(output_png_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        output_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
        
        bufferd_image = ImageIO.read(File(expected_image_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        expected_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
        
        for i in xrange(width):
            for j in xrange(height):
                exp_rgb_val = expected_image_matrix[i][j]
                result_rgb_val = output_image_matrix[i][j]
                assert exp_rgb_val == result_rgb_val
                
    def test_parse_svgfile_and_convert_to_png_background(self):
        img_proc_dir = os.path.join(helpers.APP_PATH, "test", "res", "img_proc_png")
        input_svg_path = os.path.join(img_proc_dir, "input_background.svg")
        expected_image_path = os.path.join(img_proc_dir, "expected_background.png")
        
        assert os.path.exists(input_svg_path)
        
        rotation_x, rotation_y = 255, 180
        
        output_png_path = svgtopng.convert(input_svg_path, rotation_x, rotation_y, ns_registry_lock)
        
        from javax.imageio import ImageIO
        from java.io import File
        bufferd_image = ImageIO.read(File(output_png_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        output_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
        
        bufferd_image = ImageIO.read(File(expected_image_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        expected_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
        
        for i in xrange(width):
            for j in xrange(height):
                exp_rgb_val = expected_image_matrix[i][j]
                result_rgb_val = output_image_matrix[i][j]
                assert exp_rgb_val == result_rgb_val
                
    def test_parse_svgfile_and_convert_to_png_antenna(self):
        img_proc_dir = os.path.join(helpers.APP_PATH, "test", "res", "img_proc_png")
        input_svg_path = os.path.join(img_proc_dir, "input_antenna.svg")
        expected_image_path = os.path.join(img_proc_dir, "expected_antenna.png")
        
        assert os.path.exists(input_svg_path)
        
        rotation_x, rotation_y = 53, 43
        
        output_png_path = svgtopng.convert(input_svg_path, rotation_x, rotation_y, ns_registry_lock)
        
        from javax.imageio import ImageIO
        from java.io import File
        bufferd_image = ImageIO.read(File(output_png_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        output_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
        
        bufferd_image = ImageIO.read(File(expected_image_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        expected_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
        
        for i in xrange(width):
            for j in xrange(height):
                exp_rgb_val = expected_image_matrix[i][j]
                result_rgb_val = output_image_matrix[i][j]
                assert exp_rgb_val == result_rgb_val
                  
    def test_parse_svgfile_and_convert_to_png_hat_q1(self):
        img_proc_dir = os.path.join(helpers.APP_PATH, "test", "res", "img_proc_png")
        input_svg_path = os.path.join(img_proc_dir, "input_hat.svg")
        
        assert os.path.exists(input_svg_path)
                
        rotation_x, rotation_y = 97, 51
        
        expected_image_path = os.path.join(img_proc_dir, "expected_hat" + "_rotX_" + 
                                           str(rotation_x) + "_rotY_" + str(rotation_y) + 
                                           ".png")
        
        output_png_path = svgtopng.convert(input_svg_path, rotation_x, rotation_y, ns_registry_lock)

        from javax.imageio import ImageIO
        from java.io import File
        bufferd_image = ImageIO.read(File(output_png_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        output_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]

        bufferd_image = ImageIO.read(File(expected_image_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        expected_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]

        for i in xrange(width):
            for j in xrange(height):
                exp_rgb_val = expected_image_matrix[i][j]
                result_rgb_val = output_image_matrix[i][j]
                assert exp_rgb_val == result_rgb_val
                 
    def test_parse_svgfile_and_convert_to_png_hat_q2(self):
        img_proc_dir = os.path.join(helpers.APP_PATH, "test", "res", "img_proc_png")
        input_svg_path = os.path.join(img_proc_dir, "input_hat.svg")
        
        assert os.path.exists(input_svg_path)
        
        rotation_x, rotation_y = -97, 51
        
        expected_image_path = os.path.join(img_proc_dir, "expected_hat" + "_rotX_" + 
                                           str(rotation_x) + "_rotY_" + str(rotation_y) + 
                                           ".png")
                
        output_png_path = svgtopng.convert(input_svg_path, rotation_x, rotation_y, ns_registry_lock)

        from javax.imageio import ImageIO
        from java.io import File
        bufferd_image = ImageIO.read(File(output_png_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        output_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
        
        bufferd_image = ImageIO.read(File(expected_image_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        expected_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
        
        for i in xrange(width):
            for j in xrange(height):
                exp_rgb_val = expected_image_matrix[i][j]
                result_rgb_val = output_image_matrix[i][j]
                assert exp_rgb_val == result_rgb_val
                
    def test_parse_svgfile_and_convert_to_png_hat_q3(self):
        img_proc_dir = os.path.join(helpers.APP_PATH, "test", "res", "img_proc_png")
        input_svg_path = os.path.join(img_proc_dir, "input_hat.svg")
        
        assert os.path.exists(input_svg_path)
        
        rotation_x, rotation_y = -97, -51
        
        expected_image_path = os.path.join(img_proc_dir, "expected_hat" + "_rotX_" + 
                                           str(rotation_x) + "_rotY_" + str(rotation_y) + 
                                           ".png")
        
        output_png_path = svgtopng.convert(input_svg_path, rotation_x, rotation_y, ns_registry_lock)

        from javax.imageio import ImageIO
        from java.io import File
        bufferd_image = ImageIO.read(File(output_png_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        output_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
        
        bufferd_image = ImageIO.read(File(expected_image_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        expected_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
        
        for i in xrange(width):
            for j in xrange(height):
                exp_rgb_val = expected_image_matrix[i][j]
                result_rgb_val = output_image_matrix[i][j]
                assert exp_rgb_val == result_rgb_val
                
    def test_parse_svgfile_and_convert_to_png_hat_q4(self):
        img_proc_dir = os.path.join(helpers.APP_PATH, "test", "res", "img_proc_png")
        input_svg_path = os.path.join(img_proc_dir, "input_hat.svg")
        
        assert os.path.exists(input_svg_path)
        
        rotation_x, rotation_y = 97, -51
        
        expected_image_path = os.path.join(img_proc_dir, "expected_hat" + "_rotX_" + 
                                           str(rotation_x) + "_rotY_" + str(rotation_y) + 
                                           ".png")
        
        output_png_path = svgtopng.convert(input_svg_path, rotation_x, rotation_y, ns_registry_lock)

        from javax.imageio import ImageIO
        from java.io import File
        bufferd_image = ImageIO.read(File(output_png_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        output_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
        
        bufferd_image = ImageIO.read(File(expected_image_path))
        width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
        expected_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
        
        for i in xrange(width):
            for j in xrange(height):
                exp_rgb_val = expected_image_matrix[i][j]
                result_rgb_val = output_image_matrix[i][j]
                assert exp_rgb_val == result_rgb_val

    def test_can_rewrite_svg_matrix(self):
        tree = ET.parse("test/res/scratch/Wizard_Spells/3.svg")
        root = tree.getroot()
        for child in root:
            if re.search('.*}g', child.tag) != None:
                if 'transform' in child.attrib:
                    assert(child.attrib['transform'] == "matrix(1.5902323722839355, 0, 0, 1.5902323722839355, -0.5, 0.5)")
        svgtopng._parse_and_rewrite_svg_file("test/res/scratch/Wizard_Spells/3.svg","test/res/scratch/Wizard_Spells/3_changed.svg", ns_registry_lock)
        tree = ET.parse("test/res/scratch/Wizard_Spells/3_changed.svg")
        root = tree.getroot()
        for child in root:
            if re.search('.*}g', child.tag) != None:
                if 'transform' in child.attrib:
                    assert(child.attrib['transform'] == "matrix(1, 0, 0, 1, -0.5, 0.5)")

    def test_can_rewrite_svg_text_position(self):
        tree = ET.parse("test/res/scratch/Wizard_Spells/6.svg")
        root = tree.getroot()
        for child in root:
            if re.search('.*}text', child.tag) != None:
                assert(child.attrib['x'] == '147.5')
                assert(child.attrib['y'] == '146.1')
        svgtopng._parse_and_rewrite_svg_file("test/res/scratch/Wizard_Spells/6.svg","test/res/scratch/Wizard_Spells/6_changed.svg", ns_registry_lock)
        tree = ET.parse("test/res/scratch/Wizard_Spells/6_changed.svg")
        root = tree.getroot()
        for child in root:
            if re.search('.*}text', child.tag) != None:
                assert(child.attrib['x'] == '3')
                assert(child.attrib['y'] == '24')

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

