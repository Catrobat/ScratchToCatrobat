from org.imgscalr import Scalr
from javax.imageio import ImageIO
from java.io import File


def resize_png(pngImage, width, height):
    return Scalr.resize(pngImage, Scalr.Mode.AUTOMATIC, width, height)
    
