from scratchtobat import common
import os
import subprocess

BATIK_RASTERIZER_JAR_PATH = os.path.join(common.get_project_base_path(), 'lib/batik-1.7/batik-rasterizer.jar')


def convert(input_svg_path):
    if not os.path.exists(BATIK_RASTERIZER_JAR_PATH):
        raise common.ScratchtobatError("Place batik library at {}.".format(os.path.dirname(BATIK_RASTERIZER_JAR_PATH)))
    if not isinstance(input_svg_path, (str, unicode)):
        raise common.ScratchtobatError("Input argument must be str or unicode.")
    output_png_path = input_svg_path.replace(".svg", ".png")
    print os.getcwd()
    on_error = subprocess.call(['java', '-jar', BATIK_RASTERIZER_JAR_PATH, input_svg_path])
    if on_error:
        raise common.ScratchtobatError("Extern jar call failed. See piped output.")
    return output_png_path
