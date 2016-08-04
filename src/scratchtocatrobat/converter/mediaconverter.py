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

from scratchtocatrobat import logger
from scratchtocatrobat.tools import svgtopng
from scratchtocatrobat.tools import wavconverter
from scratchtocatrobat.tools import helpers
from scratchtocatrobat import catrobat
from scratchtocatrobat import common

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
        old_src_path = self._kwargs["info"]["src_path"]
        status = self._kwargs["info"]["status"]
        if status == MediaType.UNCONVERTED_SVG:
            # converting svg to png -> new md5 and filename
            new_src_path = svgtopng.convert(old_src_path)
        elif status == MediaType.UNCONVERTED_WAV:
            # converting Android-incompatible wav to compatible wav
            new_src_path = old_src_path.replace(".wav", "_converted.wav")
            wavconverter.convert_to_android_compatible_wav(old_src_path, new_src_path)
        else:
            assert False, "Unsupported Media Type! Cannot convert media file: %s" % old_src_path
        self._kwargs["new_svg_src_paths"][old_src_path] = new_src_path
        progress_bar = self._kwargs["progress_bar"]
        if progress_bar != None: progress_bar.update()
        assert os.path.exists(new_src_path), "Not existing: {}. Available files in directory: {}".format(new_src_path, os.listdir(os.path.dirname(new_src_path)))


class MediaConverter(object):
    def __init__(self, scratch_project, catrobat_program, images_path, sounds_path):
        self.scratch_project = scratch_project
        self.catrobat_program = catrobat_program
        self.images_path = images_path
        self.sounds_path = sounds_path
        self.renamed_files_map = {}


    def _copy_media_file(self, scratch_md5_name, src_path, target_dir, is_converted_file=False):
        # for Catrobat separate file is needed for resources which are used multiple times but with different names
        for scratch_resource_name in self.scratch_project.find_all_resource_names_for(scratch_md5_name):
            catrobat_resource_file_name = catrobat_resource_file_name_for(scratch_md5_name, scratch_resource_name)
            if is_converted_file:
                original_resource_file_name = catrobat_resource_file_name
                converted_scratch_md5_name = _resource_name_for(src_path)
                catrobat_resource_file_name = catrobat_resource_file_name_for(converted_scratch_md5_name, scratch_resource_name)
                self.renamed_files_map[original_resource_file_name] = catrobat_resource_file_name
                assert catrobat_resource_file_name != original_resource_file_name # check if renamed!
            shutil.copyfile(src_path, os.path.join(target_dir, catrobat_resource_file_name))

        if is_converted_file:
            os.remove(src_path)


    def convert(self, progress_bar = None):
        all_used_resources = []
        for scratch_md5_name, src_path in self.scratch_project.md5_to_resource_path_map.iteritems():
            assert os.path.exists(src_path), "Not existing: {}. Available files in directory: {}" \
                                            .format(src_path, os.listdir(os.path.dirname(src_path)))

            if scratch_md5_name in self.scratch_project.unused_resource_names:
                log.info("Ignoring unused resource file: %s", src_path)
                if progress_bar != None: progress_bar.update()
                continue

            file_ext = os.path.splitext(scratch_md5_name)[1].lower()
            resource_info = { "scratch_md5_name": scratch_md5_name, "src_path": src_path }
            if file_ext in {".png", ".svg", ".jpg", ".gif"}:
                resource_info["dest_path"] = self.images_path
                resource_info["status"] = MediaType.IMAGE
                if file_ext == ".svg":
                    resource_info["status"] = MediaType.UNCONVERTED_SVG
            elif file_ext in {".wav", ".mp3"}:
                resource_info["dest_path"] = self.sounds_path
                resource_info["status"] = MediaType.AUDIO
                if file_ext == ".wav" and not wavconverter.is_android_compatible_wav(src_path):
                    resource_info["status"] = MediaType.UNCONVERTED_WAV
            else:
                assert file_ext in {".json"}, "Unknown media file extension: %s" % src_path
                continue
            all_used_resources.append(resource_info)

        # schedule parallel conversions (one conversion per thread)
        unconverted_types = { MediaType.UNCONVERTED_SVG, MediaType.UNCONVERTED_WAV }
        unconverted_media_resources = [res for res in all_used_resources if res["status"] in unconverted_types]

        # update progress bar for all those media files that don't have to be converted
        if progress_bar != None: [progress_bar.update() for res in all_used_resources if res["status"] not in unconverted_types]
        new_svg_src_paths = {}
        resource_index = 0
        num_total_resources = len(unconverted_media_resources)
        reference_index = 0
        while resource_index < num_total_resources:
            num_next_resources = min(MAX_CONCURRENT_THREADS, (num_total_resources - resource_index))
            next_resources_end_index = resource_index + num_next_resources
            threads = []
            for index in range(resource_index, next_resources_end_index):
                assert index == reference_index
                reference_index += 1
                info = unconverted_media_resources[index]
                kwargs = { "info": info,
                           "new_svg_src_paths": new_svg_src_paths,
                           "progress_bar": progress_bar }
                threads.append(_MediaResourceConverterThread(kwargs=kwargs))
            for thread in threads: thread.start()
            for thread in threads: thread.join()
            resource_index = next_resources_end_index
        assert reference_index == resource_index and reference_index == num_total_resources

        for resource_info in all_used_resources:
            scratch_md5_name = resource_info["scratch_md5_name"]
            src_path = resource_info["src_path"]
            src_path = new_svg_src_paths[src_path] if src_path in new_svg_src_paths else src_path # check if path changed after conversion
            dest_path = resource_info["dest_path"]
            is_converted_file = resource_info["status"] in unconverted_types
            self._copy_media_file(scratch_md5_name, src_path, dest_path, is_converted_file)

        self._rename_resource_file_names_in()


    def _rename_resource_file_names_in(self):
        number_of_converted = 0
        for look_data_or_sound_info in catrobat.media_objects_in(self.catrobat_program):
            # HACK: by accessing private field don't have to care about type
            renamed_file_name = self.renamed_files_map.get(look_data_or_sound_info.fileName)
            if renamed_file_name is not None:
                look_data_or_sound_info.fileName = renamed_file_name
                number_of_converted += 1
        assert number_of_converted >= len(self.renamed_files_map)
