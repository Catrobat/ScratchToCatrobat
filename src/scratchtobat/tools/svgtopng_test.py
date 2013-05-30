'''
Created on 25.05.2013

@author: chr
'''
from scratchtobat import testing_common
from scratchtobat.tools import svgtopng
import imghdr
import os
import unittest


class SvgToPngTest(unittest.TestCase):

    def test_can_convert_file_from_svg_to_png(self):
        input_svg_path = os.path.join(testing_common.get_test_project_path("dancing_castle"), "1.svg")
        assert os.path.exists(input_svg_path)
        svgtopng.convert(input_svg_path)
        output_png_path = input_svg_path.replace(".svg", ".png")
        self.assertTrue(os.path.exists(output_png_path))
        self.assertEqual('png', imghdr.what(output_png_path))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
