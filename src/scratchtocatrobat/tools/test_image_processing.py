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
import os
import unittest

from scratchtocatrobat.tools import common_testing
from scratchtocatrobat.tools import image_processing as img_proc
import java.awt.Font
from java.awt import Color
import java.awt.image.BufferedImage
import imghdr

# class ImageProcessingTest(common_testing.BaseTestCase):
# 
#     _allowed_font_names = ["Marker","Scratch","Gloria", "Helvetica", "Donegal", "Mystery"]
# 
#     @classmethod
#     def img_proc_pngfile_paths(cls):
#         return cls.get_test_resources_paths("img_proc_png")
# 
#     @classmethod
#     def img_proc_pngfile_output_path(cls, fileName):
#         return os.path.join(common_testing.get_test_resources_path(), "img_proc_png", fileName)
# 
#     @classmethod
#     def img_proc_jpgfile_paths(cls):
#         return cls.get_test_resources_paths("img_proc_jpg")
# 
#     @classmethod
#     def setUpClass(cls):
#         #assert len(cls.img_proc_pngfile_paths()) == 1
#         assert len(cls.img_proc_jpgfile_paths()) == 0
# 
#     def test_can_read_editable_image_from_disk(self):
#         dummy_png = self.img_proc_pngfile_paths()[0]
#         buffered_image = img_proc.read_editable_image_from_disk(dummy_png)
#         assert isinstance(buffered_image, java.awt.image.BufferedImage)
# 
#     def test_can_create_font(self):
#         for font_name in self._allowed_font_names:
#             font = img_proc.create_font(font_name, 14.0, bold=False, italic=False)
#             assert isinstance(font, java.awt.Font)
# 
#     def test_can_add_text_to_editable_image(self):
#         dummy_png = self.img_proc_pngfile_paths()[0]
#         buffered_image = img_proc.read_editable_image_from_disk(dummy_png)
#         assert isinstance(buffered_image, java.awt.image.BufferedImage)
#         font = img_proc.create_font(self._allowed_font_names[0], 14.0, bold=False, italic=False)
#         # check whether the left-outline of letter "H" in "Hello world" is NOT present in the image!
#         for i in range(0, 8):
#             rgb = buffered_image.getRGB(11, i)
#             red = rgb >> 16 & int("0x000000FF", 16)
#             green = rgb >> 8 & int("0x000000FF", 16)
#             blue = rgb & int("0x000000FF", 16)
#             assert red == 0 and green == 0 and blue == 0
#         buffered_image = img_proc.add_text_to_image(buffered_image, "Hello world!", font, Color.BLUE, 10.0, 10.0)
#         #buffered_image = img_proc.add_text_to_image(buffered_image, "Franz ist hier!?", font, Color.BLUE,10.0, 2.0)
#         # the left-outline of letter "H" in "Hello world" must NOW appear in the image!
#         for i in range(0, 8):
#             rgb = buffered_image.getRGB(11, i)
#             red = rgb >> 16 & int("0x000000FF", 16)
#             green = rgb >> 8 & int("0x000000FF", 16)
#             blue = rgb & int("0x000000FF", 16)
#             #assert red == 255 and green == 0 and blue == 0
# 
#     def test_can_save_editable_image_as_png_to_disk(self):
#         dummy_png = self.img_proc_pngfile_paths()[0]
#         buffered_image = img_proc.read_editable_image_from_disk(dummy_png)
#         assert isinstance(buffered_image, java.awt.image.BufferedImage)
#         font = img_proc.create_font(self._allowed_font_names[0], 14.0, bold=False, italic=False)
#         marker_font_value = 0
#         scratch_font_value = 1
#         gloria_font_value = 2
#         helvetica_font_value = 3
#         donegal_font_value = 4
#         mystery_font_value = 5
#         
#         marker_font =  img_proc.create_font(self._allowed_font_names[marker_font_value], 14.0, bold=False, italic=False)
#         scratch_font =  img_proc.create_font(self._allowed_font_names[scratch_font_value], 14.0, bold=False, italic=False)
#         gloria_font =  img_proc.create_font(self._allowed_font_names[gloria_font_value], 14.0, bold=False, italic=False)
#         helvetica_font =  img_proc.create_font(self._allowed_font_names[helvetica_font_value], 14.0, bold=False, italic=False)
#         donegal_font =  img_proc.create_font(self._allowed_font_names[donegal_font_value], 14.0, bold=False, italic=False)
#         mystery_font =  img_proc.create_font(self._allowed_font_names[mystery_font_value], 14.0, bold=False, italic=False)
#         
#         
#         # check whether the left-outline of letter "H" in "Hello world" is NOT present in the image!
#         for i in range(0, 8):
#             rgb = buffered_image.getRGB(11, i)
#             red = rgb >> 16 & int("0x000000FF", 16)
#             green = rgb >> 8 & int("0x000000FF", 16)
#             blue = rgb & int("0x000000FF", 16)
#             assert red == 0 and green == 0 and blue == 0
#         buffered_image = img_proc.add_text_to_image(buffered_image, "Hello world!", mystery_font, Color.RED, 10.0, 10.0)
#         buffered_image = img_proc.add_text_to_image(buffered_image, "Franz ist hier!?", marker_font, Color.BLUE,10.0, 20.0)
#         buffered_image = img_proc.add_text_to_image(buffered_image, "iloveKF", donegal_font, Color.GREEN,10.0, 32.0)
# 
# 
#         # the left-outline of letter "H" in "Hello world" must NOW appear in the image!
#         for i in range(0, 8):
#             rgb = buffered_image.getRGB(11, i)
#             red = rgb >> 16 & int("0x000000FF", 16)
#             green = rgb >> 8 & int("0x000000FF", 16)
#             blue = rgb & int("0x000000FF", 16)
#             #assert red == 255 and green == 0 and blue == 0
#         output_path = self.img_proc_pngfile_output_path("test.png")
#         try:
#             img_proc.save_editable_image_as_png_to_disk(buffered_image, output_path, overwrite=True)
#             assert os.path.isfile(output_path)
#             assert imghdr.what(output_path) == 'png'
#             # Reload the image from disk now and check if left-outline of letter "H" is still present!
#             new_buffered_image = img_proc.read_editable_image_from_disk(output_path)
#             assert isinstance(new_buffered_image, java.awt.image.BufferedImage)
#             for i in range(0, 8):
#                 rgb = new_buffered_image.getRGB(11, i)
#                 red = rgb >> 16 & int("0x000000FF", 16)
#                 green = rgb >> 8 & int("0x000000FF", 16)
#                 blue = rgb & int("0x000000FF", 16)
#                 #assert red == 255 and green == 0 and blue == 0
#         except Exception, e:
#             raise e
#         finally:
#             os.remove(output_path) # finally remove the image

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
