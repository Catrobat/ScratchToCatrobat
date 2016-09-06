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

_BATIK_CLI_JAR = "batik-rasterizer.jar"
_log = logging.getLogger(__name__)
_batik_jar_path = None


# TODO: refactor to single mediaconverter class together with wavconverter
def _checked_batik_jar_path():
#     if _BATIK_ENVIRONMENT_HOME not in os.environ:
#         raise EnvironmentError("Environment variable '{}' must be set to batik library location.".format(_BATIK_ENVIRONMENT_HOME))
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

    input_svg_URI = Paths.get(input_svg_path).toUri().toURL().toString()
    output_svg_path = input_svg_path.replace(".svg", "_modified.svg")

    if os.path.exists(output_png_path):
        _log.info("      nothing to do: '%s' already exists", output_png_path)
        # remove temporary files
        if os.path.exists(output_svg_path):
            os.remove(output_svg_path)
        return output_png_path # avoid duplicate conversions!

    png_ostream = None
    error = None
    try:
        _parse_and_rewrite_svg_file(input_svg_path, output_svg_path)
        input_svg_image = TranscoderInput(input_svg_URI)

        output_png_image = TranscoderOutput(FileOutputStream(output_png_path))

        _log.info("      converting '%s' to Pocket Code compatible png '%s'",
                  input_svg_path, output_png_path)
        png_converter = PNGTranscoder()
        png_converter.transcode(input_svg_image, output_png_image)
        assert os.path.exists(output_png_path)

# TODO: uncomment this once all remaining bugs have been fixed!
#         final_image = _translation(output_png_path, rotation_x, rotation_y)
# 
#         if final_image is None:
#             raise RuntimeError("...")
# 
#         from javax.imageio import ImageIO
#         from java.io import File
#         ImageIO.write(final_image, "PNG", File(output_png_path))
        return output_png_path
    except BaseException as err:
        import traceback
        import sys
        exc_info = sys.exc_info()
        _log.error(err)
        _log.error(traceback.format_exc())
        _log.error(exc_info)
        error = common.ScratchtobatError("PNG to SVG conversion call failed for: %s" % input_svg_path)
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
    #buffered_image = ImageIO.read(new File());
    width, height = buffered_image.getWidth(), buffered_image.getHeight()
    
    buffered_image_matrix = [[buffered_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
   
    buffered_image_matrix = _transpose_matrix(buffered_image_matrix)

    x_coords_list, y_coords_list = [], []
    
    m, n = len(buffered_image_matrix), len(buffered_image_matrix[0])
    for y in xrange(m):
        for x in xrange(n):
            pixel = buffered_image_matrix[y][x]
            if (pixel >> 24) != 0x00:
                x_coords_list.append(x)
                y_coords_list.append(y)

    _log.info("-" * 80)
    _log.info("Output path: {}".format(output_png_path))
    _log.info("height, weight: ({}, {})".format(m, n))
    start_x = min(x_coords_list) if len(x_coords_list) > 0 else 0
    end_x = max(x_coords_list) if len(x_coords_list) > 0 else 0
    start_y = min(y_coords_list) if len(y_coords_list) > 0 else 0
    end_y = max(y_coords_list) if len(y_coords_list) > 0 else 0

    _log.info("end y, end x: ({}, {})".format(end_y, end_x))

    if start_x > rotation_x:
        start_x = rotation_x
    if end_x < rotation_x:
        end_x = rotation_x
    if start_y > rotation_y:
        start_y = rotation_y
    if end_y < rotation_y:
        end_y = rotation_y

    _log.info("end y, end x: ({}, {})".format(end_y, end_x))
    _log.info("-" * 80)

    dst_new_width = end_x * 2
    dst_new_height = end_y * 2
            
    new_buffered_image = BufferedImage(dst_new_width, dst_new_height,BufferedImage.TYPE_INT_ARGB)    
    g2d = new_buffered_image.createGraphics()
    g2d.setComposite(AlphaComposite.Clear)
    g2d.fillRect(0, 0, dst_new_width, dst_new_height)

    # Bottom Right
    for old_row_y, new_row_y in zip(xrange(rotation_y, end_y + 1),xrange(end_y, dst_new_height)):
        for old_column_x, new_column_x in zip(xrange(rotation_x, end_x + 1),xrange(end_x, dst_new_width)):
            if(old_row_y >= 0 and old_column_x >= 0 and old_row_y < buffered_image_matrix.length and old_column_x < buffered_image_matrix[old_row_y].length):
                new_buffered_image.setRGB(new_column_x,new_row_y, buffered_image_matrix[old_row_y][old_column_x]);
    
    # Upper Right
    for old_row_y, new_row_y in zip(xrange(rotation_y, start_y - 1, -1),xrange(end_y, -1, -1)):
        for old_column_x, new_column_x in zip(xrange(rotation_x, end_x + 1),xrange(end_x, dst_new_width)):
            if(old_row_y >= 0 and old_column_x >= 0 and old_row_y < buffered_image_matrix.length and old_column_x < buffered_image_matrix[old_row_y].length):
                new_buffered_image.setRGB(new_column_x,new_row_y, buffered_image_matrix[old_row_y][old_column_x])
          
    # Upper Left
    for old_row_y, new_row_y in zip(xrange(rotation_y, start_y - 1, -1),xrange(end_y, -1, -1)):
        for old_column_x, new_column_x in zip(xrange(rotation_x, start_x - 1, -1),xrange(end_x, -1, -1)):
            if(old_row_y >= 0 and old_column_x >= 0 and old_row_y < buffered_image_matrix.length and old_column_x < buffered_image_matrix[old_row_y].length):
                new_buffered_image.setRGB(new_column_x,new_row_y, buffered_image_matrix[old_row_y][old_column_x])

    # Bottom Left
    for old_row_y, new_row_y in zip(xrange(rotation_y, end_y + 1),xrange(end_y, dst_new_height)):
        for old_column_x, new_column_x in zip(xrange(rotation_x, start_x - 1, -1),xrange(end_x, -1, -1)):
            if(old_row_y >= 0 and old_column_x >= 0 and old_row_y < buffered_image_matrix.length and old_column_x < buffered_image_matrix[old_row_y].length):
                new_buffered_image.setRGB(new_column_x,new_row_y, buffered_image_matrix[old_row_y][old_column_x])
                
    #color = Color.yellow
    #new_buffered_image.setRGB(end_x - 1, end_y - 1, color.getRGB())
    return new_buffered_image
    
# def _translation_to_rotation_point(img, rotation_x, rotation_y):
#    
#     dst_new_width, dst_new_height = None, None
#     half_old_width, half_old_height = None, None
#     while True:
#         dst_new_width, dst_new_height = rotation_x * 2, rotation_y * 2
#         half_old_width, half_old_height = img.getWidth() / 2, img.getHeight() / 2
#         start_x, start_y = rotation_x - half_old_height, rotation_y - half_old_width
#         end_x, end_y = rotation_x + img.getHeight() - half_old_height, rotation_y + img.getWidth() - half_old_width
#     
#         if start_x >= 0 and start_y >= 0 and end_x >= 0 and end_y >= 0:
#             break
#         else:
#             rotation_x *= 2
#             rotation_y *= 2
#             
#             
#     bufferedImage = BufferedImage(dst_new_height, dst_new_width, BufferedImage.TYPE_INT_ARGB)
#     g2d = bufferedImage.createGraphics()
#     g2d.setComposite(AlphaComposite.Clear)
#     g2d.fillRect(0, 0, dst_new_width, dst_new_height)
#     
#     img_matrix = [[img.getRGB(row_index, column_index) for column_index in xrange(img.getHeight())] for row_index in xrange(img.getWidth())]
#     
#     transposed_img_matrix = _transpose_matrix(img_matrix)
# 
#     for row_index, old_row_index in zip(xrange(start_x, end_x + 1), xrange(len(transposed_img_matrix))):
#         for column_index, old_column_index in zip(xrange(start_y, end_y + 1), xrange(len(transposed_img_matrix[0]))):
#             bufferedImage.setRGB(column_index, row_index, transposed_img_matrix[old_row_index][old_column_index])
# 
#     return bufferedImage
# 
# def _scale_image(output_png_path):
#     bufferd_image = _create_buffered_image(ImageIcon(output_png_path).getImage())
# 
#     width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
#     
#     bufferd_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
#    
#     bufferd_image_matrix = _transpose_matrix(bufferd_image_matrix)
# 
#     x_coords_list, y_coords_list = [], []
#     
#     m, n = len(bufferd_image_matrix), len(bufferd_image_matrix[0])
#     for y in xrange(m):
#         for x in xrange(n):
#             pixel = bufferd_image_matrix[y][x]
#             if (pixel >> 24) != 0x00:
#                 x_coords_list.append(x)
#                 y_coords_list.append(y)
#     
#     if len(x_coords_list) == 0 or len(y_coords_list) == 0:
#         return
# 
#     start_x, start_y = min(x_coords_list), min(y_coords_list)
#     max_x, max_y = max(x_coords_list), max(y_coords_list)  
# 
#     m, n = (max_y - start_y + 1), (max_x + 1)
#     
#     old_y_limit = len(bufferd_image_matrix)
#     old_x_limit = len(bufferd_image_matrix[0])
#     
#     new_image_matrix = [[bufferd_image_matrix[old_y][old_x]for _, old_x in zip(xrange(n), xrange(start_x, old_x_limit))] for _, old_y in zip(xrange(m),xrange(start_y,old_y_limit))]
#     
#     new_image_matrix = _transpose_matrix(new_image_matrix)        
#     
#     m, n = len(new_image_matrix), len(new_image_matrix[0])
# 
#     final_image = BufferedImage(m, n, bufferd_image.getType())
#     
#     for x in xrange(m):
#         for y in xrange(n):
#             final_image.setRGB(x, y, new_image_matrix[x][y])
#     
#     return final_image

def _transpose_matrix(matrix):
    m, n = len(matrix), len(matrix[0])
    transposed_matrix = [[matrix[y][x] for y in xrange(m)] for x in xrange(n)] 
    return transposed_matrix

    
def _create_buffered_image(image):
    result = BufferedImage(image.getWidth(None),image.getHeight(None),BufferedImage.TYPE_INT_ARGB)
    result.getGraphics().drawImage(image,0,0,None)
    return result 


def _parse_and_rewrite_svg_file(svg_input_path, svg_output_path):
    write_str = ""
    file_reader = FileReader(svg_input_path)
    buffered_reader = BufferedReader(file_reader)
    read_line = ""

    while True:
        read_line = buffered_reader.readLine()

        if read_line is None:
            break

        if "viewBox" in read_line:
            view_box_content = _get_viewbox_content(read_line)
            view_box_values = _get_viewbox_values(view_box_content)
            if view_box_values[0] != 0:
                view_box_values[2] += view_box_values[0]
                view_box_values[0] = 0

            if view_box_values[1] != 0:
                view_box_values[3] += view_box_values[1]
                view_box_values[1] = 0

            new_view_box = str(view_box_values[0]) + " " + str(view_box_values[1]) + " " + \
                           str(view_box_values[2]) + " " + str(view_box_values[3])
            read_line = re.sub(r"viewBox=\"[\-|0-9| ]+\"", "viewBox=\""
                               + new_view_box + "\"", read_line, 1)
            read_line = re.sub(r"width=\"[0-9]+\"", "width=\""+ str(view_box_values[2]) + "\"",
                               read_line, 1)
            read_line = re.sub(r"height=\"[0-9]+\"", "height=\""+ str(view_box_values[3]) + "\"",
                               read_line, 1)

        write_str += read_line + "\n"

    buffered_reader.close()
    file_reader.close()
    file_writer = PrintWriter(svg_output_path)
    file_writer.print(write_str)
    file_writer.close()


def _get_viewbox_values(view_box_str):
    view_box_values = []
    
    st = StringTokenizer(view_box_str," ")
    while st.hasMoreTokens():
        view_box_values.append(int(st.nextToken()))  
     
    return view_box_values
    
    
def _get_viewbox_content(view_box_str):
    start_view_box = view_box_str.index("viewBox") + 9
    end_view_box = view_box_str.index("\"", start_view_box)
    return view_box_str[start_view_box:end_view_box]
    

    
