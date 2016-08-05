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
from scratchtocatrobat import common
from scratchtocatrobat.tools import helpers
from java.io import FileOutputStream
from org.apache.batik.transcoder.image import PNGTranscoder
from org.apache.batik.transcoder import TranscoderInput
from org.apache.batik.transcoder import TranscoderOutput
from java.nio.file import Paths
from java.awt.image import BufferedImage
from java.awt import Image
from java.awt import AlphaComposite
from java.awt import Graphics2D
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

def convert(input_svg_path, rotation_x=36, rotation_y=67):
    assert isinstance(input_svg_path, (str, unicode))
    assert os.path.splitext(input_svg_path)[1] == ".svg"
    output_png_path = os.path.splitext(input_svg_path)[0] + ".png"

    png_ostream = None
    error = None
    try:
        # read input SVG document into Transcoder Input (use Java NIO for this purpose)
        svg_URI_input = Paths.get(input_svg_path).toUri().toURL().toString()

        _parse_and_rewrite_svg_file(svg_URI_input[5:])
        
        input_svg_image = TranscoderInput(svg_URI_input)

        # define OutputStream to PNG Image and attach to TranscoderOutputSc    
        png_ostream = FileOutputStream(output_png_path)
        
        output_png_image = TranscoderOutput(png_ostream)

        # Convert and Write output
        _log.info("      converting '%s' to Pocket Code compatible png '%s'", input_svg_path, output_png_path)
        
        my_converter = PNGTranscoder()

        my_converter.transcode(input_svg_image, output_png_image)

        assert os.path.exists(output_png_path)
        
        final_image = _scale_image(output_png_path)
        
        if final_image is None:
            raise RuntimeError("...")
        
        final_image = _translation_to_rotation_point(final_image, rotation_x, rotation_y)
        
        if final_image is None:
            raise RuntimeError("...")

        from javax.imageio import ImageIO
        from java.io import File      
        ImageIO.write(final_image, "PNG", File(output_png_path))
        
        return output_png_path
    except:
        import sys
        exc_info = sys.exc_info()
        error = common.ScratchtobatError("PNG to SVG conversion call failed for: %s" % input_svg_path)
    finally:
        # free resources
        if png_ostream != None:
            png_ostream.flush()
            png_ostream.close()

    if error != None:
        raise error
    
def _translation_to_rotation_point(img, rotation_x, rotation_y):
   
    dst_new_width, dst_new_height = None, None
    half_old_width, half_old_height = None, None
    while True:
        dst_new_width, dst_new_height = rotation_x * 2, rotation_y * 2
        half_old_width, half_old_height = img.getWidth() / 2, img.getHeight() / 2
        start_x, start_y = rotation_x - half_old_height, rotation_y - half_old_width
        end_x, end_y = rotation_x + img.getHeight() - half_old_height, rotation_y + img.getWidth() - half_old_width
    
        if start_x >= 0 and start_y >= 0 and end_x >= 0 and end_y >= 0:
            break
        else:
            rotation_x *= 2
            rotation_y *= 2
            
            
    bufferedImage = BufferedImage(dst_new_height, dst_new_width, BufferedImage.TYPE_INT_ARGB)
    g2d = bufferedImage.createGraphics()
    g2d.setComposite(AlphaComposite.Clear)
    g2d.fillRect(0, 0, dst_new_width, dst_new_height)
    
    img_matrix = [[img.getRGB(row_index, column_index) for column_index in xrange(img.getHeight())] for row_index in xrange(img.getWidth())]
    
    transposed_img_matrix = _transpose_matrix(img_matrix)
    
    #System.out.println(start_x + "|" + start_y + "\t" + start_x + "|" + end_y);
    #System.out.println(end_x + "|" + start_y + "\t" + end_x + "|" + end_y);

    for row_index, old_row_index in zip(xrange(start_x, end_x + 1), xrange(len(transposed_img_matrix))):
        for column_index, old_column_index in zip(xrange(start_y, end_y + 1), xrange(len(transposed_img_matrix[0]))):
            bufferedImage.setRGB(column_index, row_index, transposed_img_matrix[old_row_index][old_column_index])

    return bufferedImage
            
            
            
    
    
def _scale_image(output_png_path):
    bufferd_image = _create_buffered_image(ImageIcon(output_png_path).getImage())

    width, height = bufferd_image.getWidth(), bufferd_image.getHeight()
    
    bufferd_image_matrix = [[bufferd_image.getRGB(i, j) for j in xrange(height)] for i in xrange(width)]
   
    bufferd_image_matrix = _transpose_matrix(bufferd_image_matrix)

    x_coords_list, y_coords_list = [], []
    
    m, n = len(bufferd_image_matrix), len(bufferd_image_matrix[0])
    for y in xrange(m):
        for x in xrange(n):
            pixel = bufferd_image_matrix[y][x]
            if (pixel >> 24) != 0x00:
                x_coords_list.append(x)
                y_coords_list.append(y)
    
    if len(x_coords_list) == 0 or len(y_coords_list) == 0:
        return

    start_x, start_y = min(x_coords_list), min(y_coords_list)
    max_x, max_y = max(x_coords_list), max(y_coords_list)  

    m, n = (max_y - start_y + 1), (max_x + 1)
    
    old_y_limit = len(bufferd_image_matrix)
    old_x_limit = len(bufferd_image_matrix[0])
    
    new_image_matrix = [[bufferd_image_matrix[old_y][old_x]for _, old_x in zip(xrange(n), xrange(start_x, old_x_limit))] for _, old_y in zip(xrange(m),xrange(start_y,old_y_limit))]
    
    new_image_matrix = _transpose_matrix(new_image_matrix)        
    
    m, n = len(new_image_matrix), len(new_image_matrix[0])

    final_image = BufferedImage(m, n, bufferd_image.getType())
    
    for x in xrange(m):
        for y in xrange(n):
            final_image.setRGB(x, y, new_image_matrix[x][y])
    
    return final_image

def _transpose_matrix(matrix):
    m, n = len(matrix), len(matrix[0])
    transposed_matrix = [[matrix[y][x] for y in xrange(m)] for x in xrange(n)] 
    return transposed_matrix

    
def _create_buffered_image(image):
    result = BufferedImage(image.getWidth(None),image.getHeight(None),BufferedImage.TYPE_INT_ARGB)
    result.getGraphics().drawImage(image,0,0,None)
    return result 


def _parse_and_rewrite_svg_file(svg_file_path):
    write_str = ""

    file_reader = FileReader(svg_file_path)
    
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
            
            new_view_box = str(view_box_values[0]) + " " + str(view_box_values[1]) + " " + str(view_box_values[2]) + " " + str(view_box_values[3])
      
            read_line = re.sub(r"viewBox=\"[\-|0-9| ]+\"", "viewBox=\""+ new_view_box + "\"", read_line, 1)
            read_line = re.sub(r"width=\"[0-9]+\"", "width=\""+ str(view_box_values[2]) + "\"", read_line, 1)
            read_line = re.sub(r"height=\"[0-9]+\"", "height=\""+ str(view_box_values[3]) + "\"", read_line, 1)
        
        write_str += read_line + "\n"
    

    buffered_reader.close()
    file_reader.close()
    
    file_writer = PrintWriter(svg_file_path)
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
    

    
