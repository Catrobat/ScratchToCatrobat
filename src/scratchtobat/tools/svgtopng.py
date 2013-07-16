from scratchtobat import common
import os
import subprocess

# TODO: replace CLI call with API
_BATIK_ENVIRONMENT_HOME = "BATIK_HOME"
_BATIK_CLI_JAR = "batik-rasterizer.jar"


def convert(input_svg_path):
    if _BATIK_ENVIRONMENT_HOME not in os.environ:
        raise common.ScratchtobatError("Please create environment variable '{}' and set to batik library location.".format(_BATIK_ENVIRONMENT_HOME))
    batik_jar_path = os.path.join(os.environ[_BATIK_ENVIRONMENT_HOME], _BATIK_CLI_JAR)
    if not os.path.exists(batik_jar_path):
        raise common.ScratchtobatError("Jar not found: '{}'. Place batik library at {}.".format(batik_jar_path, os.path.dirname(batik_jar_path)))
    if not isinstance(input_svg_path, (str, unicode)):
        raise common.ScratchtobatError("Input argument must be str or unicode.")
    output_png_path = input_svg_path.replace(".svg", ".png")
    print os.getcwd()
    on_error = subprocess.call(['java', '-jar', batik_jar_path, input_svg_path])
    if on_error:
        raise common.ScratchtobatError("Extern jar call failed. See piped output.")
    assert os.path.exists(output_png_path)
    return output_png_path
