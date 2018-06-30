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
import logging
import os
import re
from scratchtocatrobat.tools import common
from scratchtocatrobat.tools import helpers
from java.io import FileOutputStream
from org.apache.batik.transcoder.image import PNGTranscoder
from org.apache.batik.transcoder import TranscoderInput
from org.apache.batik.transcoder import TranscoderOutput
from java.nio.file import Paths
from java.awt.image import BufferedImage
from java.awt import AlphaComposite
from java.io import BufferedReader
from java.io import FileReader
from java.io import PrintWriter
from java.util import StringTokenizer
from javax.swing import ImageIcon
import java.awt.Color
import xml.etree.cElementTree as ET


_BATIK_CLI_JAR = "batik-rasterizer.jar"
_log = logging.getLogger(__name__)
_batik_jar_path = None


# TODO: refactor to single mediaconverter class together with wavconverter
def _checked_batik_jar_path():
    batik_home_dir = helpers.config.get("PATHS", "batik_home")
    batik_jar_path = os.path.join(batik_home_dir, _BATIK_CLI_JAR)
    if not os.path.exists(batik_jar_path):
        raise EnvironmentError("Batik jar '{}' must be existing in {}.".format(batik_jar_path, os.path.dirname(batik_jar_path)))
    _batik_jar_path = batik_jar_path
    return _batik_jar_path


def convert(input_svg_path, rotation_x, rotation_y):
    assert isinstance(input_svg_path, (str, unicode))
    assert os.path.splitext(input_svg_path)[1] == ".svg"

    input_file_name = os.path.splitext(input_svg_path)[0]
    output_png_path = "{}_rotX_{}_rotY_{}.png".format(input_file_name, rotation_x, rotation_y)
    _log.info("      converting '%s' to Pocket Code compatible png '%s'", input_svg_path, output_png_path)

    output_svg_path = input_svg_path.replace(".svg", "_modified.svg")
    output_svg_URI = Paths.get(output_svg_path).toUri().toURL().toString()

    if os.path.exists(output_png_path):
        _log.error("      '%s' already exists", output_png_path)
        #assert False # "Still a Duplicate?"
        # remove temporary files
        if os.path.exists(output_svg_path):
            os.remove(output_svg_path)
        return output_png_path # avoid duplicate conversions!

    png_ostream = None
    error = None
    try:
        _parse_and_rewrite_svg_file(input_svg_path, output_svg_path)

        input_svg_image = TranscoderInput(output_svg_URI)

        output_png_image = TranscoderOutput(FileOutputStream(output_png_path))

        _log.info("      converting '%s' to Pocket Code compatible png '%s'",
                  input_svg_path, output_png_path)
        png_converter = PNGTranscoder()
        png_converter.transcode(input_svg_image, output_png_image)
        assert os.path.exists(output_png_path)

        final_image = _translation(output_png_path, rotation_x, rotation_y)

        if final_image is None:
            raise RuntimeError("...")

        from javax.imageio import ImageIO
        from java.io import File
        ImageIO.write(final_image, "PNG", File(output_png_path))
        return output_png_path
    except BaseException as err:
        import traceback
        import sys
        exc_info = sys.exc_info()
        _log.error(err)
        _log.error(traceback.format_exc())
        _log.error(exc_info)
        error = common.ScratchtobatError("SVG to PNG conversion call failed for: %s" % input_svg_path)
    finally:
        # free resources
        if png_ostream != None:
            png_ostream.flush()
            png_ostream.close()
        # remove temporary files
        if os.path.exists(output_svg_path):
            os.remove(output_svg_path)

    if error != None:
        raise error

def _translation(output_png_path, rotation_x, rotation_y):
    buffered_image = _create_buffered_image(ImageIcon(output_png_path).getImage())
    width, height = buffered_image.getWidth(), buffered_image.getHeight()

    buffered_image_matrix = [[buffered_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
    buffered_image_matrix = _transpose_matrix(buffered_image_matrix)
    m, n = len(buffered_image_matrix), len(buffered_image_matrix[0])
    _log.info("Output path: {}".format(output_png_path))

    start_x, start_y = 0, 0
    end_x, end_y = n, m

    if start_x == 0 and end_x == 0 and start_y == 0 and end_y == 0:
        _log.info("ANTENNA-ERROR")
        return buffered_image

    dst_new_width = end_x
    dst_new_height = end_y

    # overlapping x enhancement
    if (rotation_x < end_x) and (rotation_x > 0):
        if end_x - rotation_x > end_x/2:
            dst_new_width = (end_x - rotation_x) * 2
            start_x = dst_new_width/2 - rotation_x
            end_x = start_x + end_x
        elif end_x - rotation_x < end_x/2:
            end_x = 2*rotation_x
            dst_new_width = start_x + end_x

    # non-overlapping x enhancement        
    elif rotation_x  < 0:
        start_x = 2*abs(rotation_x) + end_x
        dst_new_width = 2*(abs(rotation_x) + end_x)
        end_x = start_x + end_x

    elif rotation_x >= end_x:
        dst_new_width = 2*rotation_x

    if (rotation_y < end_y) and (rotation_y > 0):
        if end_y - rotation_y > end_y/2:
            dst_new_height = (end_y - rotation_y) * 2
            start_y = dst_new_height/2 - rotation_y
            end_y = start_y + end_y
        elif end_y - rotation_y < end_y/2:
            end_y = 2*rotation_y
            dst_new_height = start_y + end_y        

    elif rotation_y  < 0:
        start_y = 2*abs(rotation_y) + end_y
        dst_new_height = 2*(abs(rotation_y) + end_y)
        end_y = start_y + end_y

    elif rotation_y >= end_y:
        dst_new_height = 2*rotation_y

    new_buffered_image = BufferedImage(dst_new_width + 1, dst_new_height + 1, BufferedImage.TYPE_INT_ARGB)
    g2d = new_buffered_image.createGraphics()
    g2d.setComposite(AlphaComposite.Clear)
    g2d.fillRect(0, 0, dst_new_width, dst_new_height)

    for row_y in xrange(start_y, end_y + 1):
        for column_x in xrange(start_x, end_x + 1):
            if row_y - start_y < buffered_image.getHeight() and column_x - start_x < buffered_image.getWidth():
                new_buffered_image.setRGB(column_x,row_y, buffered_image_matrix[row_y-start_y][column_x-start_x])
    return new_buffered_image

def _transpose_matrix(matrix):
    m, n = len(matrix), len(matrix[0])
    transposed_matrix = [[matrix[y][x] for y in xrange(m)] for x in xrange(n)] 
    return transposed_matrix


def _create_buffered_image(image):
    result = BufferedImage(image.getWidth(None),image.getHeight(None),BufferedImage.TYPE_INT_ARGB)
    result.getGraphics().drawImage(image,0,0,None)
    return result 


def _parse_and_rewrite_svg_file(svg_input_path, svg_output_path):
    tree = ET.parse(svg_input_path)
    root = tree.getroot()

    #exception is thrown if height or width is less or equal zero
    if 'height' in root.attrib and float((root.attrib['height']).replace('px', '')) <= 0:
        root.attrib['height'] = '1'
    if 'width' in root.attrib and float((root.attrib['width']).replace('px', '')) <= 0:
        root.attrib['width'] = '1'

    for child in tree.iter():
        if re.search('.*}g', child.tag) != None:
            if 'transform' in child.attrib:
                matrix_transform_attrib = child.attrib['transform']
                matrix_transform_attrib = re.sub(r"matrix\((\s?-?[0-9]+(\.[0-9]*)?,){4}", "matrix(1, 0, 0, 1,", matrix_transform_attrib)
                child.attrib['transform'] = matrix_transform_attrib

    for child in tree.iter():
        if re.search('.*}text', child.tag) != None:
            child.attrib['x'] = '3'
            child.attrib['y'] = '23'

            list_of_text_parts = (child.text).split('\n')
            child.text = (child.text).replace(child.text, '')
            namespace_tag = (child.tag).replace('text', '')
            dy_value = 0
            if 'font-size' in child.attrib:
                dy_font_size = int(child.attrib['font-size'])
            else:
                dy_font_size = 12 # default value
            for text_part in list_of_text_parts:
                ET.SubElement(child, namespace_tag + 'tspan', x = '3', dy = str(dy_value))
                dy_value = dy_value + dy_font_size
            tspan_list = child.findall(namespace_tag + 'tspan')
            for index, tspan_element in enumerate(tspan_list):
                tspan_element.text = list_of_text_parts[index]

    tree.write(svg_output_path)


def _get_viewbox_values(view_box_str):
    view_box_values = []

    st = StringTokenizer(view_box_str," ")
    while st.hasMoreTokens():
        ch = st.nextToken()
        try:
            view_box_values.append(float(ch))  
        except:
            view_box_values.append(int(ch))  
    return view_box_values


def _get_viewbox_content(view_box_str):
    start_view_box = view_box_str.index("viewBox") + 9
    end_view_box = view_box_str.index("\"", start_view_box)
    return view_box_str[start_view_box:end_view_box]

