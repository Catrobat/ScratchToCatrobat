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
import shutil
from threading import Thread
from threading import Lock
from java.awt import Color

from scratchtocatrobat.tools import logger
from scratchtocatrobat.converter import catrobat
from scratchtocatrobat.tools import common
from scratchtocatrobat.scratch.scratch import JsonKeys
from scratchtocatrobat.tools import svgtopng
from scratchtocatrobat.tools import wavconverter
from scratchtocatrobat.tools import helpers
from scratchtocatrobat.tools.helpers import ProgressType
from scratchtocatrobat.tools import image_processing
from javax.imageio import ImageIO

MAX_CONCURRENT_THREADS = int(helpers.config.get("MEDIA_CONVERTER", "max_concurrent_threads"))
log = logger.log
ns_registry_lock = Lock()


class MediaType(object):
    IMAGE = 1
    AUDIO = 2
    UNCONVERTED_SVG = 3
    UNCONVERTED_WAV = 4


class _MediaResourceConverterThread(Thread):

    def run(self):
        old_src_path = self._kwargs["data"]["src_path"]
        media_type = self._kwargs["data"]["media_type"]
        info = self._kwargs["data"]["info"]

        if media_type == MediaType.UNCONVERTED_SVG:
            # converting svg to png -> new md5 and filename
            new_src_path = svgtopng.convert(old_src_path, info["rotationCenterX"], info["rotationCenterY"], ns_registry_lock)
        elif media_type == MediaType.UNCONVERTED_WAV:
            # converting Android-incompatible wav to compatible wav
            new_src_path = wavconverter.convert_to_android_compatible_wav(old_src_path)
        else:
            assert False, "Unsupported Media Type! Cannot convert media file: %s" % old_src_path

        self._kwargs["new_src_paths"][old_src_path] = new_src_path
        progress_bar = self._kwargs["progress_bar"]
        if progress_bar != None:
            progress_bar.update(ProgressType.CONVERT_MEDIA_FILE)
        assert os.path.exists(new_src_path), "Not existing: {}. Available files in directory: {}" \
               .format(new_src_path, os.listdir(os.path.dirname(new_src_path)))


class MediaConverter(object):

    def __init__(self, scratch_project, catrobat_program, images_path, sounds_path):
        self.scratch_project = scratch_project
        self.catrobat_program = catrobat_program
        self.images_path = images_path
        self.sounds_path = sounds_path
        self.file_rename_map = {}

    def convert(self, progress_bar=None):
        all_used_resources = []
        unconverted_media_resources = []
        converted_media_resources_paths = set()

        # TODO: remove this block later {
        for scratch_md5_name, src_path in self.scratch_project.md5_to_resource_path_map.iteritems():
            if scratch_md5_name in self.scratch_project.unused_resource_names:
                log.info("Ignoring unused resource file: %s", src_path)
                if progress_bar != None:
                    progress_bar.update(ProgressType.CONVERT_MEDIA_FILE)
                continue
        # }

        for scratch_object in self.scratch_project.objects:
            self.setup_costume_info(scratch_object, all_used_resources, unconverted_media_resources,
                                    converted_media_resources_paths, progress_bar)
            self.setup_sound_info(scratch_object, all_used_resources, unconverted_media_resources,
                                  converted_media_resources_paths, progress_bar)

        new_src_paths = self.conversion_svgtopng_wav(unconverted_media_resources, progress_bar)
        converted_media_files_to_be_removed = set()
        duplicate_filename_set = set()
        self.resource_info_setup(all_used_resources, duplicate_filename_set, new_src_paths, converted_media_resources_paths)
        self.rename_media_files_and_copy()

        # delete converted png files -> only temporary saved
        for media_file_to_be_removed in converted_media_files_to_be_removed:
            os.remove(media_file_to_be_removed)

    def setup_costume_info(self, defined_scratch_object, all_used_resources, unconverted_media_resources,
                           converted_media_resources_paths, progress_bar):
        threads = []
        for costume_info in defined_scratch_object.get_costumes():
            costume_dict = self.get_info(costume_info[JsonKeys.COSTUME_MD5], True)

            assert os.path.exists(costume_dict["costume_src_path"]), "Not existing: {}".format(costume_dict["costume_src_path"])
            assert costume_dict["file_ext"] in {".png", ".svg", ".jpg", ".gif"}, \
                "Unsupported image file extension: %s" % costume_dict["costume_src_path"]
            ispng = costume_dict["file_ext"] == ".png"
            is_unconverted = costume_dict["file_ext"] == ".svg"
            self.setup_resource_info_dict(costume_dict["costume_file_name"], costume_dict["costume_src_path"], is_unconverted, costume_info,
                                          all_used_resources, unconverted_media_resources, converted_media_resources_paths,
                                          progress_bar, threads, ispng, True)
        for thread in threads: thread.start()
        for thread in threads: thread.join()

    def setup_sound_info(self, defined_scratch_object, all_used_resources, unconverted_media_resources, converted_media_resources_paths, progress_bar):
        for sound_info in defined_scratch_object.get_sounds():
            sound_dict = self.get_info(sound_info[JsonKeys.SOUND_MD5])
            assert os.path.exists(sound_dict["sound_src_path"]), "Not existing: {}".format(sound_dict["sound_src_path"])
            assert sound_dict["file_ext"] in {".wav", ".mp3"}, "Unsupported sound file extension: %s" % sound_dict["sound_src_path"]
            is_unconverted = sound_dict["file_ext"] == ".wav" and not wavconverter.is_android_compatible_wav(sound_dict["sound_src_path"])

            self.setup_resource_info_dict(sound_dict["sound_file_name"], sound_dict["sound_src_path"], is_unconverted, sound_info,
                                          all_used_resources, unconverted_media_resources, converted_media_resources_paths,
                                          progress_bar, [])

    def get_info(self, file_name, is_costume=False):
        if is_costume:
            costume_info = {"costume_file_name": file_name,
                            "costume_src_path": os.path.join(self.scratch_project.project_base_path, file_name),
                            "file_ext": os.path.splitext(file_name)[1].lower()}
            if not os.path.exists(costume_info["costume_src_path"]):
            # media files of local projects are NOT named by their hash-value -> change name
                costume_info["costume_src_path"] = self.scratch_project.md5_to_resource_path_map[file_name]
            return costume_info
        else:
            sound_info = {"sound_file_name": file_name,
                          "sound_src_path": os.path.join(self.scratch_project.project_base_path, file_name),
                          "file_ext": os.path.splitext(file_name)[1].lower()}
            if not os.path.exists(sound_info["sound_src_path"]):
                sound_info["sound_src_path"] = self.scratch_project.md5_to_resource_path_map[file_name]
            return sound_info

    def setup_resource_info_dict(self, file_name, src_path, is_unconverted, info, all_used_resources,
                                 unconverted_media_resources, converted_media_resources_paths, progress_bar,
                                 threads, ispng=False, is_costume=False):
        if is_costume:
            media_type = MediaType.UNCONVERTED_SVG if is_unconverted else MediaType.IMAGE
        else:
            media_type = MediaType.UNCONVERTED_WAV if is_unconverted else MediaType.AUDIO

        resource_info = {
            "scratch_md5_name": file_name,
            "src_path": src_path,
            "dest_path": self.images_path if is_costume else self.sounds_path,
            "media_type": media_type,
            "info": info
        }
        all_used_resources.append(resource_info)
        if is_unconverted:
            unconverted_media_resources.append(resource_info)
        elif progress_bar is not None and src_path not in converted_media_resources_paths:
            # update progress bar for all those media files that don't have to be converted
            #TODO: background gets scaled too, shouldn't be the case
            if ispng:
                 threads.append(Thread(target=self.multi_thread_convert, args=(info, src_path, converted_media_resources_paths, progress_bar)))
                 return
            converted_media_resources_paths.add(src_path)
            progress_bar.update(ProgressType.CONVERT_MEDIA_FILE)

    def conversion_svgtopng_wav(self, unconverted_media_resources, progress_bar):
        # schedule concurrent conversions (one conversion per thread)
        new_src_paths = {}
        resource_index = 0
        num_total_resources = len(unconverted_media_resources)
        reference_index = 0
        media_srces = []
        while resource_index < num_total_resources:
            num_next_resources = min(MAX_CONCURRENT_THREADS, (num_total_resources - resource_index))
            next_resources_end_index = resource_index + num_next_resources
            threads = []
            for index in range(resource_index, next_resources_end_index):
                assert index == reference_index
                reference_index += 1
                data = unconverted_media_resources[index]
                if data["src_path"] in media_srces:
                    continue
                else:
                    media_srces.append(data["src_path"])
                kwargs = {
                    "data": data,
                    "new_src_paths": new_src_paths,
                    "progress_bar": progress_bar
                }
                threads.append(_MediaResourceConverterThread(kwargs=kwargs))
            for thread in threads: thread.start()
            for thread in threads: thread.join()
            resource_index = next_resources_end_index
        assert reference_index == resource_index and reference_index == num_total_resources
        return new_src_paths

    def resource_info_setup(self, all_used_resources, duplicate_filename_set, new_src_paths, converted_media_files_to_be_removed):
        for resource_info in all_used_resources:
            # reconstruct the temporary catrobat filenames -> catrobat.media_objects_in(self.catrobat_file)
            current_filename = helpers.create_catrobat_md5_filename(resource_info["scratch_md5_name"], duplicate_filename_set)
            # check if path changed after conversion
            old_src_path = resource_info["src_path"]
            src_path = new_src_paths[old_src_path] if old_src_path in new_src_paths else old_src_path
            if resource_info["media_type"] in { MediaType.IMAGE, MediaType.UNCONVERTED_SVG }:
                costume_info = resource_info["info"]
                if "text" in costume_info:
                    self.font_setup(costume_info, src_path)

            current_basename, _ = os.path.splitext(current_filename)
            self.file_rename_map[current_basename] = {}
            self.file_rename_map[current_basename]["src_path"] = src_path
            self.file_rename_map[current_basename]["dst_path"] = resource_info["dest_path"]
            self.file_rename_map[current_basename]["media_type"] = resource_info["media_type"]

            if resource_info["media_type"] in { MediaType.UNCONVERTED_SVG, MediaType.UNCONVERTED_WAV }:
                converted_media_files_to_be_removed.add(src_path)

    def font_setup(self, costume_info, src_path):
            text = costume_info[JsonKeys.COSTUME_TEXT]
            x, y, width, height = costume_info[JsonKeys.COSTUME_TEXT_RECT]
            # TODO: extract RGBA
            # text_color = costume_info[JsonKeys.COSTUME_TEXT_COLOR]
            font_name = "NO FONT"
            font_style = "regular"
            font_scaling_factor = costume_info[JsonKeys.COSTUME_RESOLUTION] if JsonKeys.COSTUME_RESOLUTION in costume_info else 1
            if len(costume_info[JsonKeys.COSTUME_FONT_NAME].split()) == 2:
                [font_name, font_style] = costume_info[JsonKeys.COSTUME_FONT_NAME].split()
            else:
                log.warning("font JSON parameters wrong '{0}', replacing with known font '{1}'".format(costume_info[JsonKeys.COSTUME_FONT_NAME], image_processing._supported_fonts_path_mapping.keys()[0]))
                font_scaling_factor = font_scaling_factor * 1.1 # the original font might be smaller, better scale it down than cut it off
            if(font_name not in image_processing._supported_fonts_path_mapping):
                log.warning("font name '{0}' unknown, replacing with known font '{1}'".format(font_name, image_processing._supported_fonts_path_mapping.keys()[0]))
                font_name = image_processing._supported_fonts_path_mapping.keys()[0]
                font_scaling_factor = font_scaling_factor * 1.1 # the original font might be smaller, better scale it down than cut it off
            is_bold = font_style == "Bold"
            is_italic = font_style == "Italic"
            font_size = float(costume_info[JsonKeys.COSTUME_FONT_SIZE]) / float(font_scaling_factor)
            image_file_path = src_path
            font = image_processing.create_font(font_name, font_size, is_bold, is_italic)
            assert font is not None
            editable_image = image_processing.read_editable_image_from_disk(image_file_path)
            fonty = float(y) + (height * float(font_scaling_factor) / 2.0) # I think this might not work if we rotate something outside of the picture
            editable_image = image_processing.add_text_to_image(editable_image, text, font, Color.BLACK, float(x), float(fonty), float(width), float(height))

            # TODO: create duplicate...
            # TODO: move test_converter.py to converter-python-package...
            image_processing.save_editable_image_as_png_to_disk(editable_image, image_file_path, overwrite=True)

    def multi_thread_convert(self, info, src_path, converted_media_resources_paths, progress_bar):
        self.convertPNG(info, src_path, src_path)
        converted_media_resources_paths.add(src_path)
        progress_bar.update(ProgressType.CONVERT_MEDIA_FILE)

    # rename the media files and copy them to the catrobat project directory
    def rename_media_files_and_copy(self):

        def create_new_file_name(provided_file, index_helper, file_type):
            _, ext = os.path.splitext(provided_file)
            if file_type in {MediaType.UNCONVERTED_SVG, MediaType.IMAGE}:
                return "img_#" + str(index_helper.assign_image_index()) + ext
            else:
                return "snd_#" + str(index_helper.assign_sound_index()) + ext

        media_file_index_helper = helpers.MediaFileIndex()
        for info in catrobat.media_objects_in(self.catrobat_program):
            basename, _ = os.path.splitext(info.fileName)

            # ignore these files, already correctly provided by the converter
            if any(x in basename for x in ["key", "mouse", "slider", "list_handle_"]):
                continue

            assert basename in self.file_rename_map and \
                "src_path" in self.file_rename_map[basename] and \
                "dst_path" in self.file_rename_map[basename] and \
                "media_type" in self.file_rename_map[basename]


            src_path = self.file_rename_map[basename]["src_path"]
            dst_path = self.file_rename_map[basename]["dst_path"]
            media_type = self.file_rename_map[basename]["media_type"]
            new_file_name = create_new_file_name(src_path, media_file_index_helper, media_type)
            shutil.copyfile(src_path, os.path.join(dst_path, new_file_name))
            info.fileName = new_file_name

    def resize_png(self, path_in, path_out, bitmapResolution):
        import java.awt.image.BufferedImage
        import java.io.File
        import java.io.IOException
        input = java.io.File(path_in)
        image = ImageIO.read(input)
        from math import ceil
        new_height = int(ceil(image.getHeight() / float(bitmapResolution)))
        new_height = new_height if new_height > 2 else 2
        new_width = int(ceil(image.getWidth() / float(bitmapResolution)))
        new_width = new_width if new_width > 2 else 2
        def resize(img, height, width):
            tmp = img.getScaledInstance(width, height, java.awt.Image.SCALE_SMOOTH)
            resized = java.awt.image.BufferedImage(width, height, java.awt.image.BufferedImage.TYPE_INT_ARGB)
            g2d = resized.createGraphics()
            g2d.drawImage(tmp, 0, 0, None)
            g2d.dispose()
            empty = True
            for x in range(new_width):
                for y in range(new_height):
                    alpha = (resized.getRGB(x,y) >> 24) & 0xff
                    if alpha > 0:
                        empty = False
                        break
                if not empty:
                    break
            if empty:
                argb = (80 << 24) | (0x00FF00)
                resized.setRGB(0,0,argb)
                resized.setRGB(0,1,argb)
                resized.setRGB(1,1,argb)
                resized.setRGB(1,0,argb)
            return resized
        resized = resize(image, new_height, new_width)
        output = java.io.File(path_out)
        ImageIO.write(resized, "png", output)
        return path_out

    def convertPNG(self, costume_info, costume_src_path , costume_dest_path):
        import java.io.File
        new_image = svgtopng._translation(costume_src_path, costume_info["rotationCenterX"], costume_info["rotationCenterY"])
        ImageIO.write(new_image, "png", java.io.File(costume_dest_path))
        if JsonKeys.COSTUME_RESOLUTION in costume_info:
            self.resize_png(costume_dest_path, costume_dest_path, costume_info[JsonKeys.COSTUME_RESOLUTION])