#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2015 The Catrobat Team
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

import logging
import os
from java.io import File
from javax.imageio import ImageIO
from java.awt.image import BufferedImage
from java.awt import Font
from java.awt import Color
import imghdr
from scratchtocatrobat import common

log = logging.getLogger(__name__)
_supported_image_file_types = ['gif', 'jpeg', 'png']
_supported_fonts_path_mapping = { 'Helvetica' : {
    'regular': 'nimbus-sans-l/nimbus-sans-l_regular.ttf',
    'bold': 'nimbus-sans-l/nimbus-sans-l_bold.ttf',
    'italic': 'nimbus-sans-l/nimbus-sans-l_italic.ttf',
    'bold-italic': 'nimbus-sans-l/nimbus-sans-l_bold-italic.ttf'
}}

def read_editable_image_from_disk(path):
    assert os.path.isfile(path)
    assert imghdr.what(path) in _supported_image_file_types
    return ImageIO.read(File(path))

def create_font(font_name, size, bold=False, italic=False):
    assert font_name in _supported_fonts_path_mapping
    assert isinstance(size, float)

    font_base_path = os.path.join(common.get_project_base_path(), 'resources', 'fonts')
    fonts = _supported_fonts_path_mapping[font_name]
    if bold and italic:
        font_path = os.path.join(font_base_path, fonts['bold-italic'])
    elif bold:
        font_path = os.path.join(font_base_path, fonts['bold'])
    elif italic:
        font_path = os.path.join(font_base_path, fonts['italic'])
    else:
        font_path = os.path.join(font_base_path, fonts['regular'])
    assert os.path.isfile(font_path)

    font = Font.createFont(Font.TRUETYPE_FONT, File(font_path))
    return font.deriveFont(size)

def add_text_to_image(editable_image, text, font, color, x, y):
    assert isinstance(editable_image, BufferedImage), "No *editable* image (instance of ImageIO) given!"
    assert len(text) > 0, "No or empty text given..."
    assert isinstance(font, Font), "No valid font given! Should be instance of java.awt.Font!"
    assert isinstance(color, Color), "No valid color given! Should be instance of java.awt.Color!"
    assert isinstance(x, float)
    assert isinstance(y, float)

    g = editable_image.getGraphics()
    g.setFont(font)
    g.setColor(color)
    g.drawString(text, x, y)
    g.dispose()
    return editable_image

def save_editable_image_as_png_to_disk(editable_image, path, overwrite=False):
    assert isinstance(editable_image, BufferedImage), "No *editable* image (instance of ImageIO) given!"
    assert overwrite == True or os.path.isfile(path) == False, "File already exists"
    ImageIO.write(editable_image, "png", File(path))
