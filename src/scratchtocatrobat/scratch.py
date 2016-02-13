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
from __future__ import print_function

import glob
import itertools
import json
import os
import sys
import urllib2

from scratchtocatrobat import common
from scratchtocatrobat import scratchwebapi

_log = common.log

_PROJECT_FILE_NAME = "project.json"

class JsonKeys(object):
    BASELAYER_ID = "baseLayerID"
    CHILDREN = "children"
    COSTUME_MD5 = "baseLayerMD5"
    COSTUME_RESOLUTION = "bitmapResolution"
    COSTUME_NAME = "costumeName"
    COSTUMES = "costumes"
    INFO = "info"
    PROJECT_ID = 'projectID'
    OBJECT_NAME = "objName"
    SCRIPTS = "scripts"
    SOUND_MD5 = "md5"
    SOUND_ID = "soundID"
    SOUND_NAME = "soundName"
    SOUNDS = "sounds"
    LISTS = "lists"
    VARIABLES = 'variables'

#PROJECT_SPECIFIC_KEYS = ["info", "currentCostumeIndex", "penLayerMD5", "tempoBPM", "videoAlpha", "children"]
PROJECT_SPECIFIC_KEYS = ["info", "currentCostumeIndex", "penLayerMD5", "tempoBPM", "children"]
SCRIPT_GREEN_FLAG, SCRIPT_RECEIVE, SCRIPT_KEY_PRESSED, SCRIPT_SENSOR_GREATER_THAN, SCRIPT_SCENE_STARTS, SCRIPT_CLICKED = SCRIPTS = \
    ["whenGreenFlag", "whenIReceive", "whenKeyPressed", "whenSensorGreaterThan", "whenSceneStarts", "whenClicked", ]
STAGE_OBJECT_NAME = "Stage"
STAGE_WIDTH_IN_PIXELS = 480
STAGE_HEIGHT_IN_PIXELS = 360


# TODO: rename
class Object(common.DictAccessWrapper):

    def __init__(self, object_data):
        if not self.is_valid_class_input(object_data):
            raise ObjectError("Input is no valid Scratch object.")
        for key in (JsonKeys.SOUNDS, JsonKeys.COSTUMES, JsonKeys.SCRIPTS, JsonKeys.LISTS, JsonKeys.VARIABLES):
            if key not in object_data:
                object_data[key] = []
        super(Object, self).__init__(object_data)
        self.scripts = [Script(_) for _ in self.get_scripts() if Script.is_valid_script_input(_)]
        number_of_ignored_scripts = len(self.get_scripts()) - len(self.scripts)
        if number_of_ignored_scripts > 0:
            _log.debug("Ignored %s scripts", number_of_ignored_scripts)
        self._preprocess_object()

    def _preprocess_object(self):
        from scratchtocatrobat import converter
        preprocessed_scripts = []
        additional_scripts = []
        for script_number, script in enumerate(self.scripts):
            preprocessed_blocks = []
            blocks_iterator = iter(script.blocks)
            for block_number, block in enumerate(blocks_iterator):
                block_name, block_parameters = block[0], block[1:]
                # WORKAROUND: as long there are no equivalent Catrobat bricks
                if block_name in {"doUntil", "doWaitUntil"}:
                    do_until_condition, [do_until_blocks] = block_parameters[0], block_parameters[1:] if block_name == "doUntil" else [["wait:elapsed:from:", 0.0001]]
                    loop_done_variable = converter.generated_variable_name("_".join([self['objName'], block_name, str(script_number), str(block_number)]))
                    broadcast_msg = loop_done_variable + "_msg"
                    loop_blocks = [["doIfElse", ["not", do_until_condition], do_until_blocks, [["broadcast:", broadcast_msg], ["setVar:to:", loop_done_variable, 1]]]]
                    loop_guard = ["doIf", ["not", ["=", ["readVariable", loop_done_variable], 1]], loop_blocks]
                    replacement_blocks = [["setVar:to:", loop_done_variable, 0], ["doForever", [loop_guard]]]
                    preprocessed_blocks += replacement_blocks
                    after_loop_raw_script = [0, 0, [["whenIReceive", broadcast_msg]] + [block for block in blocks_iterator]]
                    additional_scripts += [Script(after_loop_raw_script)]
                else:
                    preprocessed_blocks += [block]
            # TODO: improve
            script.raw_script[1:] = preprocessed_blocks
            script = Script([0, 0, script.raw_script])
            preprocessed_scripts += [script]
        self.scripts = preprocessed_scripts + additional_scripts

    @classmethod
    def is_valid_class_input(cls, object_data):
        return 'objName' in object_data

    def is_stage(self):
        # TODO: extend and consolidate with verify in RawProject
        return self.get_info() is not None

    def __iter__(self):
        return iter(self.scripts)


class RawProject(Object):
    """
    Represents the raw Scratch project structure.
    """

    def __init__(self, dict_, data_origin="<undefined>"):
        super(RawProject, self).__init__(dict_)
        assert self.is_stage()
        self._verify_scratch_dictionary(dict_, data_origin)
        self.dict_ = dict_
        self.raw_objects = [child for child in self.get_children() if "objName" in child]
        self.objects = [Object(raw_object) for raw_object in [dict_] + self.raw_objects]
        self.resource_names = [self._resource_name_from(raw_resource) for raw_resource in self._raw_resources()]
        self.unique_resource_names = list(set(self.resource_names))

    def __iter__(self):
        return iter(self.objects)

    def number_of_resources(self):
        return len(self.resource_names)

    def _verify_scratch_dictionary(self, dict_, data_origin):
        if self.contains_info():
            data_origin = self.get_info().get("projectID")
        # FIXME: check which tags are really required
        for key in PROJECT_SPECIFIC_KEYS:
            if key not in dict_:
                raise UnsupportedProjectFileError("In project file from: '{}' key='{}' must be set.".format(data_origin, key))

    def _raw_resources(self):
        return itertools.chain(*(object_.get_sounds() + object_.get_costumes() for object_ in self.objects))

    def _resource_name_from(self, raw_resource):
        assert JsonKeys.SOUND_MD5 in raw_resource or JsonKeys.COSTUME_MD5 in raw_resource
        md5_file_name = raw_resource[JsonKeys.SOUND_MD5] if JsonKeys.SOUND_NAME in raw_resource else raw_resource[JsonKeys.COSTUME_MD5]
        return md5_file_name

    ''' Compute total number of iterations for progress bar
        (assuming the resources have to be downloaded via Scratch's WebAPI) '''
    def num_of_iterations_of_downloaded_project(self, progress_bar):
        unique_resource_names = self.unique_resource_names
        num_total_resources = len(unique_resource_names)
        num_of_additional_downloads = num_total_resources + 1 # includes project.json download

        # update progress weight
        result = self.num_of_iterations_of_local_project(progress_bar) - progress_bar.saving_xml_progress_weight
        result += num_of_additional_downloads
        percentage = float(progress_bar.SAVING_XML_PROGRESS_WEIGHT_PERCENTAGE)/100.0
        progress_bar.saving_xml_progress_weight = int(round((percentage * float(result))/(1.0-percentage)))
        return (result + progress_bar.saving_xml_progress_weight)

    ''' Compute total number of iterations for progress bar
        (assuming all resources already exist locally in a directory) '''
    def num_of_iterations_of_local_project(self, progress_bar):
        unique_resource_names = self.unique_resource_names
        num_total_unique_resources = len(unique_resource_names)
        num_of_downloads = 2 # for fetching title and description (2 different requests!)
        objects_scripts = [obj.scripts for obj in self.objects]
        all_scripts = reduce(lambda obj1_scripts, obj2_scripts: obj1_scripts + obj2_scripts, objects_scripts)
        num_of_scripts = len(all_scripts)
        num_of_resource_file_conversions = num_total_unique_resources
        result = num_of_downloads + num_of_scripts + num_of_resource_file_conversions
        percentage = float(progress_bar.SAVING_XML_PROGRESS_WEIGHT_PERCENTAGE)/100.0
        progress_bar.saving_xml_progress_weight = int(round((percentage * float(result))/(1.0-percentage)))
        return (result + progress_bar.saving_xml_progress_weight)

    @staticmethod
    def raw_project_code_from_project_folder_path(project_folder_path):
        json_file_path = os.path.join(project_folder_path, _PROJECT_FILE_NAME)
        if not os.path.exists(json_file_path):
            raise EnvironmentError("Project file not found: {!r}. Please create.".format(json_file_path))
        with open(json_file_path) as fp:
            try:
                return json.load(fp)
            except:
                # guess if binary file, since Scratch 1.x stores data in binary instead of JSON
                textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
                is_binary_string = lambda bytesdata: bool(bytesdata.translate(None, textchars))
                fp.seek(0, 0) # set file pointer back to the beginning of the file
                if is_binary_string(fp.read(1024)): # check first 1024 bytes
                    raise EnvironmentError("Invalid JSON file. The project's code-file "\
                            "seems to be a binary file. Project might be very old "\
                            "Scratch project. Scratch projects lower than 2.0 are "\
                            "not supported!")
                else:
                    raise EnvironmentError("Invalid JSON file. But the project's "\
                                           "code-file seems to be no binary file...")

    @classmethod
    def from_project_folder_path(cls, project_folder_path):
        return cls(cls.raw_project_code_from_project_folder_path(project_folder_path))

    @classmethod
    def from_project_code_content(cls, code_content, origin="<undefined>"):
        try:
            parsed_json = json.loads(code_content)
        except ValueError, e:
            raise ProjectCodeError("No or corrupt JSON (%s): %s" % (origin, e))
        return cls(parsed_json)


# FIXME: do not inherit from RawProject
class Project(RawProject):
    """
    Represents a complete Scratch project including all resource files.
    """

    def __init__(self, project_base_path, name=None, id_=None, progress_bar=None):
        def read_md5_to_resource_path_mapping():
            md5_to_resource_path_map = {}
            # TODO: clarify that only files with extension are covered
            for project_file_path in glob.glob(os.path.join(project_base_path, "*.*")):
                resource_name = common.md5_hash(project_file_path) + os.path.splitext(project_file_path)[1]
                md5_to_resource_path_map[resource_name] = project_file_path
            try:
                # penLayer is no regular resource file
                del md5_to_resource_path_map[self['penLayerMD5']]
            except KeyError:
                # TODO: include penLayer download in webapi
                pass
            return md5_to_resource_path_map

        def verify_resources(resources):
            for res_dict in resources:
                assert JsonKeys.SOUND_MD5 in res_dict or JsonKeys.COSTUME_MD5 in res_dict
                md5_file = res_dict[JsonKeys.SOUND_MD5] if JsonKeys.SOUND_NAME in res_dict else res_dict[JsonKeys.COSTUME_MD5]
                resource_md5 = os.path.splitext(md5_file)[0]
                if md5_file not in self.md5_to_resource_path_map:
                    raise ProjectError("Missing resource file at project: {}. Provide resource with md5: {}".format(project_base_path, resource_md5))

        super(Project, self).__init__(self.raw_project_code_from_project_folder_path(project_base_path))
        self.project_base_path = project_base_path
        if id_ is not None:
            self.project_id = id_
        else:
            self.project_id = self.get_info().get("projectID")

        if not self.project_id:
            self.project_id = "0"
            name = "Untitled"
            self.description = None
            #raise ProjectError("No project id specified in project file. Please provide project id with constructor.")
        else:
            self.description = scratchwebapi.request_project_description_for(self.project_id)
        if progress_bar != None: progress_bar.update() # description step passed

        if name is not None:
            self.name = name
        else:
            # FIXME: for some projects no project info available
            try:
                self.name = scratchwebapi.request_project_name_for(self.project_id)
            except urllib2.HTTPError:
                self.name = str(self.project_id)
                self.description = None
        if progress_bar != None: progress_bar.update() # name step passed
        self.name = self.name.strip()
        self.md5_to_resource_path_map = read_md5_to_resource_path_mapping()
        assert self['penLayerMD5'] not in self.md5_to_resource_path_map
        for scratch_object in self.objects:
            # TODO: rename to verify_object?
            verify_resources(scratch_object.get_sounds() + scratch_object.get_costumes())

        self.global_user_lists = [scratch_obj.get_lists() for scratch_obj in self.objects if scratch_obj.is_stage()][0]

        listened_keys = []
        for scratch_obj in self.objects:
            for script in scratch_obj.scripts:
                if script.type == SCRIPT_KEY_PRESSED:
                    assert len(script.arguments) == 1
                    listened_keys += script.arguments
        self.listened_keys = set(listened_keys)
        # TODO: rename
        self.background_md5_names = set([costume[JsonKeys.COSTUME_MD5] for costume in self.get_costumes()])
        self.unused_resource_names, self.unused_resource_paths = common.pad(zip(*self.find_unused_resources_name_and_filepath()), 2, [])
        for unused_path in self.unused_resource_paths:
            _log.warning("Project folder contains unused resource file: '%s'. These will be omitted for Catrobat project.", os.path.basename(unused_path))

    def find_unused_resources_name_and_filepath(self):
        # TODO: remove duplication with __init__
        for file_path in glob.glob(os.path.join(self.project_base_path, "*.*")):
            md5_resource_filename = common.md5_hash(file_path) + os.path.splitext(file_path)[1]
            if md5_resource_filename not in self.resource_names:
                if os.path.basename(file_path) != _PROJECT_FILE_NAME:
                    yield md5_resource_filename, file_path

    def find_all_resource_names_for(self, resource_unique_id):
        resource_names = set()
        for raw_resource in self._raw_resources():
            if resource_unique_id in set([raw_resource.get(JsonKeys.SOUND_MD5), raw_resource.get(JsonKeys.COSTUME_MD5)]):
                resource_names.update([raw_resource[JsonKeys.COSTUME_NAME if JsonKeys.COSTUME_NAME in raw_resource else JsonKeys.SOUND_NAME]])
        return list(resource_names)


# TODO: rename
class Script(object):

    def __init__(self, script_input):
        if not self.is_valid_script_input(script_input):
            raise ScriptError("Input is no valid Scratch script.")
        self.raw_script = script_input[2]
        script_block, self.blocks = self.raw_script[0], self.raw_script[1:]
        if not self.blocks:
            _log.debug("Empty script: %s", script_input)
        self.script_element = ScriptElement.from_raw_block(self.blocks)
        assert isinstance(self.script_element, BlockList)
        self.type, self.arguments = script_block[0], script_block[1:]
        # FIXME: never reached as is_valid_script_input() fails before
        if self.type not in SCRIPTS:
            raise ScriptError("Unknown Scratch script type: {}".format(self.type))

    @classmethod
    def is_valid_script_input(cls, json_input):
        if (isinstance(json_input, list) and len(json_input) == 3 and all(isinstance(positional_value, (int, float)) for positional_value in json_input[0:2]) and isinstance(json_input[2], list)):
            # NOTE: could use a json validator instead
            script_content = json_input[2]
            if script_content[0][0] in SCRIPTS:
                return True
        return False

    def get_type(self):
        return self.type


class ScriptElement(object):

    def __init__(self, name=None, arguments=None):
        if arguments is None:
            arguments = []
        self.name = name
        self.children = []
        for argument in arguments:
            self.add(self.from_raw_block(argument))

    def add(self, first, *arguments):
        self.children.extend(itertools.chain((first,), arguments))

    def __iter__(self):
        return iter(self.children)

    def prettyprint(self, indent="", file_=sys.stdout):
        print("{} {}".format(indent, self.name), file=file_)
        for child in self:
            child.prettyprint(indent + "    ", file_=file_)

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    @classmethod
    def from_raw_script(cls, raw_script):
        script = Script(raw_script)
        return cls.from_raw_block(script.blocks)

    @classmethod
    def from_raw_block(cls, raw_block):
        block_name = None
        block_arguments = []
        if isinstance(raw_block, list):
            is_block_list = len(raw_block) == 0 or isinstance(raw_block[0], list)
            if not is_block_list:
                block_name, block_arguments = raw_block[0], raw_block[1:]
                assert isinstance(block_name, (str, unicode)), "Raw block: %s" % raw_block
                Class = Block
            else:
                block_arguments = raw_block
                Class = BlockList
        else:
            block_name = raw_block
            Class = BlockValue
        return Class(block_name, arguments=block_arguments)


class Block(ScriptElement):
    pass


class BlockList(ScriptElement):

    def __init__(self, *args, **kwargs):
        super(BlockList, self).__init__(*args, **kwargs)
        self.name = "<LIST>"


class BlockValue(ScriptElement):
    pass


class AbstractBlocksTraverser(object):

    def traverse(self, script_element):
        assert isinstance(script_element, ScriptElement)
        # depth first traversing
        for child in script_element:
            self.traverse(child)
        self._visit(script_element)

    def _visit(self, script_element):
        raise NotImplementedError


class UnsupportedProjectFileError(common.ScratchtobatError):
    pass


class ProjectCodeError(common.ScratchtobatError):
    pass


class ProjectError(common.ScratchtobatError):
    pass


class ObjectError(common.ScratchtobatError):
    pass


class ScriptError(common.ScratchtobatError):
    pass
