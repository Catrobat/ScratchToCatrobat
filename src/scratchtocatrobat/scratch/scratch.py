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
from __future__ import print_function

import glob
import itertools
import json
import os
import sys

from scratchtocatrobat.tools import common
from scratchtocatrobat.scratch import scratchwebapi
from scratchtocatrobat.tools import helpers
from scratchtocatrobat.tools.helpers import ProgressType
from scratchtocatrobat.scratch import scriptcodemodifier

_log = common.log

_PROJECT_FILE_NAME = helpers.scratch_info("code_file_name")

class JsonKeys(object):
    BASELAYER_ID = "baseLayerID"
    CHILDREN = "children"
    COSTUME_MD5 = "baseLayerMD5"
    COSTUME_RESOLUTION = "bitmapResolution"
    COSTUME_NAME = "costumeName"
    COSTUME_TEXT = "text"
    COSTUME_TEXT_RECT = "textRect"
    COSTUME_TEXT_COLOR = "textColor"
    COSTUME_FONT_NAME = "fontName"
    COSTUME_FONT_SIZE = "fontSize"
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
SCRIPT_GREEN_FLAG, SCRIPT_RECEIVE, SCRIPT_KEY_PRESSED, SCRIPT_SENSOR_GREATER_THAN, SCRIPT_SCENE_STARTS, SCRIPT_CLICKED, SCRIPT_PROC_DEF = SCRIPTS = \
    ["whenGreenFlag", "whenIReceive", "whenKeyPressed", "whenSensorGreaterThan", "whenSceneStarts", "whenClicked", "procDef"]
STAGE_OBJECT_NAME = "Stage"
STAGE_WIDTH_IN_PIXELS = 480
STAGE_HEIGHT_IN_PIXELS = 360
S2CC_TIMER_VARIABLE_NAME = "S2CC_timer"
S2CC_TIMER_RESET_BROADCAST_MESSAGE = "S2CC_reset_timer"
S2CC_POSITION_X_VARIABLE_NAME_PREFIX = "S2CC_position_x_"
S2CC_POSITION_Y_VARIABLE_NAME_PREFIX = "S2CC_position_y_"
ADD_TIMER_SCRIPT_KEY = "add_timer_script_key"
ADD_TIMER_RESET_SCRIPT_KEY = "add_timer_reset_script_key"
ADD_POSITION_SCRIPT_TO_OBJECTS_KEY = "add_position_script_to_objects_key"


def verify_resources_of_scratch_object(scratch_object, md5_to_resource_path_map, project_base_path):
    scratch_object_resources = scratch_object.get_sounds() + scratch_object.get_costumes()
    for res_dict in scratch_object_resources:
        assert JsonKeys.SOUND_MD5 in res_dict or JsonKeys.COSTUME_MD5 in res_dict
        md5_file = res_dict[JsonKeys.SOUND_MD5] if JsonKeys.SOUND_NAME in res_dict else res_dict[JsonKeys.COSTUME_MD5]
        resource_md5 = os.path.splitext(md5_file)[0]
        if md5_file not in md5_to_resource_path_map:
            raise ProjectError("Missing resource file at project: {}. Provide resource with md5: {}"
                               .format(project_base_path, resource_md5))

# TODO: rename
class Object(common.DictAccessWrapper):

    def __init__(self, object_data):
        if not self.is_valid_class_input(object_data):
            raise ObjectError("Input is no valid Scratch object.")
        for key in (JsonKeys.SOUNDS, JsonKeys.COSTUMES, JsonKeys.SCRIPTS, JsonKeys.LISTS, JsonKeys.VARIABLES):
            if key not in object_data:
                object_data[key] = []
        super(Object, self).__init__(object_data)
        self.name = self.get_objName()
        self.scripts = [Script(script) for script in self.get_scripts() if Script.is_valid_script_input(script)]
        number_of_ignored_scripts = len(self.get_scripts()) - len(self.scripts)
        if number_of_ignored_scripts > 0:
            _log.debug("Ignored %s scripts", number_of_ignored_scripts)

    def preprocess_object(self, all_sprite_names):
        workaround_info = {
            ADD_TIMER_SCRIPT_KEY: False,
            ADD_TIMER_RESET_SCRIPT_KEY: False,
            ADD_POSITION_SCRIPT_TO_OBJECTS_KEY: set()
        }

        ############################################################################################
        # timer and timerReset workaround
        ############################################################################################
        def has_timer_block(block_list):
            for block in block_list:
                if isinstance(block, list) and (block[0] == 'timer' or has_timer_block(block)):
                    return True
            return False

        def has_timer_reset_block(block_list):
            for block in block_list:
                if isinstance(block, list) and (block[0] == 'timerReset' or has_timer_reset_block(block)):
                    return True
            return False

        def replace_timer_blocks(block_list):
            new_block_list = []
            for block in block_list:
                if isinstance(block, list):
                    if block[0] == 'timer':
                        new_block_list += [["readVariable", S2CC_TIMER_VARIABLE_NAME]]
                    elif block[0] == 'timerReset':
                        new_block_list += [["doBroadcastAndWait", S2CC_TIMER_RESET_BROADCAST_MESSAGE]]
                    else:
                        new_block_list += [replace_timer_blocks(block)]
                else:
                    new_block_list += [block]
            return new_block_list

        for script in self.scripts:
            if has_timer_reset_block(script.blocks): workaround_info[ADD_TIMER_RESET_SCRIPT_KEY] = True
            if has_timer_block(script.blocks): workaround_info[ADD_TIMER_SCRIPT_KEY] = True

            script.blocks = replace_timer_blocks(script.blocks)

            # parse again ScriptElement tree
            script.script_element = ScriptElement.from_raw_block(script.blocks)

        ############################################################################################
        # distance to object workaround
        ############################################################################################
        def has_distance_to_object_block(block_list, all_sprite_names):
            for block in block_list:
                if isinstance(block, list) \
                and ((block[0] == 'distanceTo:' and block[1] in all_sprite_names) \
                     or has_distance_to_object_block(block, all_sprite_names)):
                    return True
            return False

        def replace_distance_to_object_blocks(block_list, positions_needed_for_sprite_names):
            new_block_list = []
            for block in block_list:
                if isinstance(block, list):
                    if block[0] == 'distanceTo:':
                        # euclidean distance (Pythagorean theorem) to compute distance
                        # between both sprite objects
                        new_block_list += [
                            ["computeFunction:of:", "sqrt", ["+",
                              ["*",
                                ["()", ["-", ["xpos"], ["readVariable", S2CC_POSITION_X_VARIABLE_NAME_PREFIX + block[1]]]],
                                ["()", ["-", ["xpos"], ["readVariable", S2CC_POSITION_X_VARIABLE_NAME_PREFIX + block[1]]]]
                              ], ["*",
                                ["()", ["-", ["ypos"], ["readVariable", S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + block[1]]]],
                                ["()", ["-", ["ypos"], ["readVariable", S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + block[1]]]]
                              ]
                            ]]
                        ]
                        positions_needed_for_sprite_names.add(block[1])
                    else:
                        new_block_list += [replace_distance_to_object_blocks(block, positions_needed_for_sprite_names)]
                else:
                    new_block_list += [block]
            return new_block_list

        positions_needed_for_sprite_names = set()
        for script in self.scripts:
            if has_distance_to_object_block(script.blocks, all_sprite_names):
                script.blocks = replace_distance_to_object_blocks(script.blocks, positions_needed_for_sprite_names)
            # parse again ScriptElement tree
            script.script_element = ScriptElement.from_raw_block(script.blocks)
        workaround_info[ADD_POSITION_SCRIPT_TO_OBJECTS_KEY] = positions_needed_for_sprite_names

        return workaround_info

    @classmethod
    def is_valid_class_input(cls, object_data):
        return JsonKeys.OBJECT_NAME in object_data

    def is_stage(self):
        # TODO: extend and consolidate with verify in RawProject
        return self.get_info() != None

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

        # preprocessing
        add_timer_script = False
        add_timer_reset_script = False
        sprite_name_sprite_mapping = dict(map(lambda obj: (obj.get_objName(), obj), self.objects))
        all_sprite_names = sprite_name_sprite_mapping.keys()
        position_script_to_be_added = set()
        for scratch_object in self.objects:
            workaround_info = scratch_object.preprocess_object(all_sprite_names)
            if workaround_info[ADD_TIMER_SCRIPT_KEY]: add_timer_script = True
            if workaround_info[ADD_TIMER_RESET_SCRIPT_KEY]: add_timer_reset_script = True
            position_script_to_be_added |= workaround_info[ADD_POSITION_SCRIPT_TO_OBJECTS_KEY]

        if add_timer_script: self._add_timer_script_to_stage_object()
        if add_timer_script and add_timer_reset_script: self._add_timer_reset_script_to_stage_object()
        for destination_sprite_name in position_script_to_be_added:
            sprite_object = sprite_name_sprite_mapping[destination_sprite_name]
            assert sprite_object is not None
            self._add_update_position_script_to_object(sprite_object)

    def _add_update_position_script_to_object(self, sprite_object):
        # add global variables for positions!
        position_x_var_name = S2CC_POSITION_X_VARIABLE_NAME_PREFIX + sprite_object.get_objName()
        position_y_var_name = S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + sprite_object.get_objName()
        global_variables = self.objects[0]._dict_object["variables"]
        global_variables.append({
            "name": position_x_var_name,
            "value": 0,
            "isPersistent": False
        })
        global_variables.append({
            "name": position_y_var_name,
            "value": 0,
            "isPersistent": False
        })
        # update position script
        script_blocks = [
            ["doForever", [
              ["setVar:to:", position_x_var_name, ["xpos"]],
              ["setVar:to:", position_y_var_name, ["ypos"]],
              ["wait:elapsed:from:", 0.03]
            ]]
        ]
        sprite_object.scripts += [Script([0, 0, [[SCRIPT_GREEN_FLAG]] + script_blocks])]

    def _add_timer_script_to_stage_object(self):
        assert len(self.objects) > 0
        # add timer variable to stage object (in Scratch this acts as a global variable)
        self.objects[0]._dict_object["variables"].append({
            "name": S2CC_TIMER_VARIABLE_NAME,
            "value": 0,
            "isPersistent": False
        })
        # timer counter script
        script_blocks = [
            ["doForever", [
              ["changeVar:by:", S2CC_TIMER_VARIABLE_NAME, 0.1],
              ["wait:elapsed:from:", 0.1]
            ]]
        ]
        self.objects[0].scripts += [Script([0, 0, [[SCRIPT_GREEN_FLAG]] + script_blocks])]

    def _add_timer_reset_script_to_stage_object(self):
        assert len(self.objects) > 0
        # timer reset script
        script_blocks = [["setVar:to:", S2CC_TIMER_VARIABLE_NAME, 0]]
        self.objects[0].scripts += [Script([0, 0, [[SCRIPT_RECEIVE, S2CC_TIMER_RESET_BROADCAST_MESSAGE]] + script_blocks])]

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

    ''' Compute total number of iterations and assign to progress bar
        (assuming the resources have to be downloaded via Scratch's WebAPI) '''
    def expected_progress_of_downloaded_project(self, progress_bar):
        unique_resource_names = self.unique_resource_names
        num_total_resources = len(unique_resource_names)
        num_of_additional_downloads = num_total_resources + 1 # includes project.json download

        # update progress weight
        expected_progress = self.expected_progress_of_local_project(progress_bar)
        result = expected_progress.sum() - progress_bar.saving_xml_progress_weight
        result += num_of_additional_downloads
        percentage = float(progress_bar.SAVING_XML_PROGRESS_WEIGHT_PERCENTAGE)/100.0
        progress_bar.saving_xml_progress_weight = int(round((percentage * float(result))/(1.0-percentage)))
        expected_progress.iterations[ProgressType.DOWNLOAD_CODE] = 1
        expected_progress.iterations[ProgressType.DOWNLOAD_MEDIA_FILE] = num_total_resources
        expected_progress.iterations[ProgressType.SAVE_XML] = progress_bar.saving_xml_progress_weight
        return expected_progress

    ''' Compute total number of iterations and assign to progress bar
        (assuming all resources already exist locally in a directory) '''
    def expected_progress_of_local_project(self, progress_bar):
        unique_resource_names = self.unique_resource_names
        num_total_unique_resources = len(unique_resource_names)
        objects_scripts = [obj.scripts for obj in self.objects]
        all_scripts = reduce(lambda obj1_scripts, obj2_scripts: obj1_scripts + obj2_scripts, objects_scripts)
        num_of_scripts = len(all_scripts)
        num_of_resource_file_conversions = num_total_unique_resources
        result = num_of_scripts + num_of_resource_file_conversions
        percentage = float(progress_bar.SAVING_XML_PROGRESS_WEIGHT_PERCENTAGE)/100.0
        progress_bar.saving_xml_progress_weight = int(round((percentage * float(result))/(1.0-percentage)))
        return helpers.Progress(0, 1, 0, num_of_resource_file_conversions, num_of_scripts,
                                progress_bar.saving_xml_progress_weight)

    @staticmethod
    def raw_project_code_from_project_folder_path(project_folder_path):
        json_file_path = os.path.join(project_folder_path, _PROJECT_FILE_NAME)
        if not os.path.exists(json_file_path):
            raise EnvironmentError("Project file not found: {!r}. Please create.".format(json_file_path))
        with open(json_file_path) as fp:
            try:
                return json.load(fp)
            except:
                # guess if is binary file, since Scratch 1.x saves project data in a binary file
                # instead of a JSON file like in 2.x
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


class Project(RawProject):
    """
    Represents a complete Scratch project including all resource files.
    """

    def __init__(self, project_base_path, name=None, id_=None, progress_bar=None):
        def read_md5_to_resource_path_mapping():
            md5_to_resource_path_map = {}
            # TODO: clarify that only files with extension are covered
            for res_file_path in glob.glob(os.path.join(project_base_path, "*.*")):
                resource_name = common.md5_hash(res_file_path) + os.path.splitext(res_file_path)[1]
                md5_to_resource_path_map[resource_name] = res_file_path
            try:
                # penLayer is no regular resource file
                del md5_to_resource_path_map[self['penLayerMD5']]
            except KeyError:
                # TODO: include penLayer download in webapi
                pass
            assert self['penLayerMD5'] not in md5_to_resource_path_map
            return md5_to_resource_path_map

        super(Project, self).__init__(self.raw_project_code_from_project_folder_path(project_base_path))
        self.project_base_path = project_base_path

        if id_ != None:
            self.project_id = id_
        else:
            self.project_id = self.get_info().get("projectID")

        if not self.project_id:
            self.project_id = "0"
            self.name = name if name is not None else "Untitled"
            self.instructions = self.notes_and_credits = None
            self.automatic_screenshot_image_url = None
        else:
            self.name = name if name is not None else scratchwebapi.request_project_title_for(self.project_id)
            self.instructions = scratchwebapi.request_project_instructions_for(self.project_id)
            self.notes_and_credits = scratchwebapi.request_project_notes_and_credits_for(self.project_id)
            self.automatic_screenshot_image_url = scratchwebapi.request_project_image_url_for(self.project_id)

        if progress_bar != None: progress_bar.update(ProgressType.DETAILS) # details step passed

        _log.info("Scratch project: %s%s", self.name,
                  "(ID: {})".format(self.project_id) if self.project_id > 0 else "")

        self.name = self.name.strip() if self.name != None else "Unknown Project"
        self.md5_to_resource_path_map = read_md5_to_resource_path_mapping()
        self.global_user_lists = self.objects[0].get_lists()

        for scratch_object in self.objects:
            verify_resources_of_scratch_object(scratch_object, self.md5_to_resource_path_map,
                                               self.project_base_path)

        listened_keys = []
        for scratch_obj in self.objects:
            for script in scratch_obj.scripts:
                if script.type == SCRIPT_KEY_PRESSED:
                    assert len(script.arguments) == 1
                    listened_keys += script.arguments
        self.listened_keys = set(listened_keys)

        # TODO: rename
        self.background_md5_names = set([costume[JsonKeys.COSTUME_MD5] for costume in self.get_costumes()])

        result = self.find_unused_resources_name_and_filepath()
        self.unused_resource_names = result[0] if len(result) > 0 else []
        self.unused_resource_paths = result[1] if len(result) > 0 else []

        for unused_path in self.unused_resource_paths:
            _log.warning("Project folder contains unused resource file: '%s'. These " \
                         "will be omitted for Catrobat project.",
                         os.path.basename(unused_path))

    def find_unused_resources_name_and_filepath(self):
        # TODO: remove duplication with __init__
        result = []
        for file_path in glob.glob(os.path.join(self.project_base_path, "*.*")):
            md5_resource_filename = common.md5_hash(file_path) + os.path.splitext(file_path)[1]
            if md5_resource_filename not in self.resource_names:
                if os.path.basename(file_path) != _PROJECT_FILE_NAME:
                    result += [(md5_resource_filename, file_path)]
        return map(list, zip(*result))

    def find_all_resource_names_for(self, resource_unique_id):
        resource_names = set()
        for raw_resource in self._raw_resources():
            if resource_unique_id in set([raw_resource.get(JsonKeys.SOUND_MD5), raw_resource.get(JsonKeys.COSTUME_MD5)]):
                resource_names.update([raw_resource[JsonKeys.COSTUME_NAME if JsonKeys.COSTUME_NAME in raw_resource else JsonKeys.SOUND_NAME]])
        return list(resource_names)


class Script(object):

    def __init__(self, script_input):
        if not self.is_valid_script_input(script_input):
            raise ScriptError("Input is no valid Scratch script.")
        self.raw_script = script_input[2] # TODO: remove this...
        script_block, self.blocks = self.raw_script[0], self.raw_script[1:]
        if not self.blocks:
            _log.debug("Empty script: %s", script_input)

        # TODO: add them dynamically!
        for injector in [scriptcodemodifier.ZeroifyEmptyValuesModifier(), scriptcodemodifier.InjectMissingBracketsModifier()]:
            self.blocks = injector.modify(self.blocks)

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

    def __eq__(self, other):
        if self.type != other.type: return False

        def cmp_arguments(arguments, other_arguments):
            for (index, arg) in enumerate(arguments):
                other_arg = other_arguments[index]
                if isinstance(arg, list):
                    if not cmp_arguments(arg, other_arg):
                        return False
                elif isinstance(arg, (str, unicode, float, int)):
                    if arg != other_arg:
                        return False
                else:
                    assert False, "Unexpected script argument type %s" % type(arg)
            return True

        if not cmp_arguments(self.arguments, other.arguments):
            return False

        def cmp_block(block, other_block):
            if isinstance(block[0], list):
                if not isinstance(other_block[0], list): return False
                block = block[0]
                other_block = other_block[0]

            assert isinstance(block[0], (str, unicode))
            assert isinstance(other_block[0], (str, unicode))

            if block[0] != other_block[0]: return False
            block_args = block[1:]
            other_block_args = other_block[1:]

            for (block_arg_index, block_arg) in enumerate(block_args):
                other_block_arg = other_block_args[block_arg_index]
                if type(block_arg) != type(other_block_arg) \
                and not (isinstance(block_arg, (str, unicode)) and isinstance(block_arg, (str, unicode))):
                    return False

                if isinstance(block_arg, list):
                    if not cmp_block(block_arg, other_block_arg):
                        return False
                elif isinstance(block_arg, (str, unicode, float, int)):
                    if block_arg != other_block_arg:
                        return False
                else:
                    assert False, "Unexpected type %s" % type(block_arg)
            return True

        assert isinstance(self.blocks, list)
        assert isinstance(other.blocks, list)

        if len(other.blocks) != len(self.blocks):
            return False

        for (index, block) in enumerate(self.blocks):
            other_block = other.blocks[index]
            assert isinstance(block, list)
            assert isinstance(other_block, list)
            if not cmp_block(block, other_block):
                return False

        return True

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
        # recursively create ScriptElement tree
        block_name = None
        block_arguments = []
        if isinstance(raw_block, list):
            is_block_list = len(raw_block) == 0 or isinstance(raw_block[0], list)
            if not is_block_list:
                block_name, block_arguments = raw_block[0], raw_block[1:]
                assert isinstance(block_name, (str, unicode)), "Raw block: %s" % raw_block
                clazz = Block
            else:
                block_arguments = raw_block
                clazz = BlockList
        else:
            block_name = raw_block
            clazz = BlockValue

        return clazz(block_name, arguments=block_arguments)


class Block(ScriptElement):

    def __init__(self, *args, **kwargs):
        super(Block, self).__init__(*args, **kwargs)


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
