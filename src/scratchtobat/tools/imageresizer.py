from org.imgscalr import Scalr


def resize_png(pngImage, width, height):
    return Scalr.resize(pngImage, Scalr.Mode.AUTOMATIC, width, height)  # @UndefinedVariable (problem with Scalr.Mode)
