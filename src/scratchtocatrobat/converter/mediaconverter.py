#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2016 The Catrobat Team
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

MAX_CONCURRENT_THREADS = int(helpers.config.get("MEDIA_CONVERTER", "max_concurrent_threads"))
log = logger.log


class MediaType(object):
    IMAGE = 1
    AUDIO = 2
    UNCONVERTED_SVG = 3
    UNCONVERTED_WAV = 4


def catrobat_resource_file_name_for(scratch_md5_name, scratch_resource_name):
    assert os.path.basename(scratch_md5_name) == scratch_md5_name \
    and len(os.path.splitext(scratch_md5_name)[0]) == 32, \
    "Must be MD5 hash with file ext: " + scratch_md5_name

    # remove unsupported unicode characters from filename
#     if isinstance(scratch_resource_name, unicode):
#         scratch_resource_name = unicodedata.normalize('NFKD', scratch_resource_name).encode('ascii','ignore')
#         if (scratch_resource_name == None) or (len(scratch_resource_name) == 0):
#             scratch_resource_name = "unicode_replaced"
    resource_ext = os.path.splitext(scratch_md5_name)[1]
    return scratch_md5_name.replace(resource_ext, "_" + scratch_resource_name + resource_ext)


def _resource_name_for(file_path):
    return common.md5_hash(file_path) + os.path.splitext(file_path)[1]


class _MediaResourceConverterThread(Thread):

    def run(self):
        old_src_path = self._kwargs["data"]["src_path"]
        media_type = self._kwargs["data"]["media_type"]
        info = self._kwargs["data"]["info"]

        if media_type == MediaType.UNCONVERTED_SVG:
            # converting svg to png -> new md5 and filename
            new_src_path = svgtopng.convert(old_src_path, info["rotationCenterX"], info["rotationCenterY"])
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
        self.renamed_files_map = {}


    def convert(self, progress_bar = None):
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
            project_base_path = self.scratch_project.project_base_path

            for costume_info in scratch_object.get_costumes():
                costume_file_name = costume_info[JsonKeys.COSTUME_MD5]
                costume_src_path = os.path.join(project_base_path, costume_file_name)
                file_ext = os.path.splitext(costume_file_name)[1].lower()

                if not os.path.exists(costume_src_path):
                    # media files of local projects are NOT named by their hash-value -> change name
                    costume_src_path = self.scratch_project.md5_to_resource_path_map[costume_file_name]

                assert os.path.exists(costume_src_path), "Not existing: {}".format(costume_src_path)
                assert file_ext in {".png", ".svg", ".jpg", ".gif"}, \
                       "Unsupported image file extension: %s" % costume_src_path

                is_unconverted = file_ext == ".svg"
                resource_info = {
                    "scratch_md5_name": costume_file_name,
                    "src_path": costume_src_path,
                    "dest_path": self.images_path,
                    "media_type": MediaType.UNCONVERTED_SVG if is_unconverted else MediaType.IMAGE,
                    "info": costume_info
                }

                all_used_resources.append(resource_info)

                if is_unconverted:
                    unconverted_media_resources.append(resource_info)
                elif progress_bar != None and costume_src_path not in converted_media_resources_paths:
                    # update progress bar for all those media files that don't have to be converted
                    progress_bar.update(ProgressType.CONVERT_MEDIA_FILE)
                    converted_media_resources_paths.add(costume_src_path)

            for sound_info in scratch_object.get_sounds():
                sound_file_name = sound_info[JsonKeys.SOUND_MD5]
                sound_src_path = os.path.join(project_base_path, sound_file_name)
                file_ext = os.path.splitext(sound_file_name)[1].lower()

                if not os.path.exists(sound_src_path):
                    # media files of local projects are NOT named by their hash-value -> change name
                    sound_src_path = self.scratch_project.md5_to_resource_path_map[sound_file_name]

                assert os.path.exists(sound_src_path), "Not existing: {}".format(sound_src_path)
                assert file_ext in {".wav", ".mp3"}, "Unsupported sound file extension: %s" % sound_src_path

                is_unconverted = file_ext == ".wav" and not wavconverter.is_android_compatible_wav(sound_src_path)
                resource_info = {
                    "scratch_md5_name": sound_file_name,
                    "src_path": sound_src_path,
                    "dest_path": self.sounds_path,
                    "media_type": MediaType.UNCONVERTED_WAV if is_unconverted else MediaType.AUDIO,
                    "info": sound_info
                }

                all_used_resources.append(resource_info)

                if is_unconverted:
                    unconverted_media_resources.append(resource_info)
                elif progress_bar != None and sound_src_path not in converted_media_resources_paths:
                    # update progress bar for all those media files that don't have to be converted
                    progress_bar.update(ProgressType.CONVERT_MEDIA_FILE)
                    converted_media_resources_paths.add(sound_src_path)


        # schedule concurrent conversions (one conversion per thread)
        new_src_paths = {}
        resource_index = 0
        num_total_resources = len(unconverted_media_resources)
        reference_index = 0
        all_unconverted_src_media_paths = set()
        while resource_index < num_total_resources:
            num_next_resources = min(MAX_CONCURRENT_THREADS, (num_total_resources - resource_index))
            next_resources_end_index = resource_index + num_next_resources
            threads = []
            for index in range(resource_index, next_resources_end_index):
                assert index == reference_index
                reference_index += 1
                data = unconverted_media_resources[index]
                should_update_progress_bar = not data["src_path"] in all_unconverted_src_media_paths
                all_unconverted_src_media_paths.add(data["src_path"])
                kwargs = {
                    "data": data,
                    "new_src_paths": new_src_paths,
                    "progress_bar": progress_bar if should_update_progress_bar else None
                }
                threads.append(_MediaResourceConverterThread(kwargs=kwargs))
            for thread in threads: thread.start()
            for thread in threads: thread.join()
            resource_index = next_resources_end_index
        assert reference_index == resource_index and reference_index == num_total_resources

        converted_media_files_to_be_removed = set()
        for resource_info in all_used_resources:
            scratch_md5_name = resource_info["scratch_md5_name"]

            # check if path changed after conversion
            old_src_path = resource_info["src_path"]
            if old_src_path in new_src_paths:
                src_path = new_src_paths[old_src_path]
            else:
                src_path = old_src_path

            if resource_info["media_type"] in { MediaType.IMAGE, MediaType.UNCONVERTED_SVG }:
                costume_info = resource_info["info"]
                if "text" in costume_info:
                    text = costume_info[JsonKeys.COSTUME_TEXT]
                    x, y, width, height = costume_info[JsonKeys.COSTUME_TEXT_RECT]
                    # TODO: extract RGBA
                    # text_color = costume_info[JsonKeys.COSTUME_TEXT_COLOR]
                    [font_name, font_style] = costume_info[JsonKeys.COSTUME_FONT_NAME].split()
                    is_bold = font_style == "Bold"
                    is_italic = font_style == "Italic"
                    font_size = float(costume_info[JsonKeys.COSTUME_FONT_SIZE])
                    image_file_path = src_path
                    font = image_processing.create_font(font_name, font_size, is_bold, is_italic)
                    assert font is not None
                    editable_image = image_processing.read_editable_image_from_disk(image_file_path)
                    editable_image = image_processing.add_text_to_image(editable_image, text, font, Color.BLACK, float(x), float(y), float(width), float(height))
                    # TODO: create duplicate...
                    # TODO: move test_converter.py to converter-python-package...
                    image_processing.save_editable_image_as_png_to_disk(editable_image, image_file_path, overwrite=True)

            self._copy_media_file(scratch_md5_name, src_path, resource_info["dest_path"],
                                  resource_info["media_type"])

            if resource_info["media_type"] in { MediaType.UNCONVERTED_SVG, MediaType.UNCONVERTED_WAV }:
                converted_media_files_to_be_removed.add(src_path)

        self._update_file_names_of_converted_media_files()

        for media_file_to_be_removed in converted_media_files_to_be_removed:
            os.remove(media_file_to_be_removed)


    def _update_file_names_of_converted_media_files(self):
        for (old_file_name, new_file_name) in self.renamed_files_map.iteritems():
            look_data_or_sound_infos = filter(lambda info: info.fileName == old_file_name,
                                      catrobat.media_objects_in(self.catrobat_program))
            assert len(look_data_or_sound_infos) > 0

            for info in look_data_or_sound_infos:
                info.fileName = new_file_name


    def _copy_media_file(self, scratch_md5_name, src_path, dest_path, media_type):
        # for Catrobat separate file is needed for resources which are used multiple times but with different names
        for scratch_resource_name in self.scratch_project.find_all_resource_names_for(scratch_md5_name):
            new_file_name = catrobat_resource_file_name_for(scratch_md5_name, scratch_resource_name)
            if media_type in { MediaType.UNCONVERTED_SVG, MediaType.UNCONVERTED_WAV }:
                old_file_name = new_file_name
                converted_scratch_md5_name = _resource_name_for(src_path)
                new_file_name = catrobat_resource_file_name_for(converted_scratch_md5_name,
                                                                scratch_resource_name)
                assert new_file_name != old_file_name # check if renamed!
                self.renamed_files_map[old_file_name] = new_file_name

            shutil.copyfile(src_path, os.path.join(dest_path, new_file_name))

