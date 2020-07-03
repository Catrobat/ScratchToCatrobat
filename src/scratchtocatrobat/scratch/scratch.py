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
from __future__ import print_function

import glob
import itertools
import json
import os
import sys
from operator import itemgetter

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
    SCRIPT_COMMENTS = "scriptComments"
    SOUND_MD5 = "md5"
    SOUND_ID = "soundID"
    SOUND_NAME = "soundName"
    SOUNDS = "sounds"
    LISTS = "lists"
    VARIABLES = 'variables'
    TARGETS = 'targets'

#PROJECT_SPECIFIC_KEYS = ["info", "currentCostumeIndex", "penLayerMD5", "tempoBPM", "videoAlpha", "children"]
PROJECT_SPECIFIC_KEYS = ["info", "currentCostumeIndex", "penLayerMD5", "tempoBPM", "children"]
SCRIPT_GREEN_FLAG, SCRIPT_RECEIVE, SCRIPT_KEY_PRESSED, SCRIPT_SENSOR_GREATER_THAN, SCRIPT_SCENE_STARTS, SCRIPT_CLICKED, SCRIPT_PROC_DEF, SCRIPT_CLONED, SCRIPT_WHEN_BACKGROUND_SWITCHES_TO = SCRIPTS = \
    ["whenGreenFlag", "whenIReceive", "whenKeyPressed", "whenSensorGreaterThan", "whenSceneStarts", "whenClicked", "procDef", "whenCloned", "whenSceneStarts"]
STAGE_OBJECT_NAME = "Stage"
STAGE_WIDTH_IN_PIXELS = 480
STAGE_HEIGHT_IN_PIXELS = 360
S2CC_KEY_VARIABLE_NAME = "S2CC:key_"
S2CC_TIMER_VARIABLE_NAME = "S2CC:timer"
S2CC_TIMER_RESET_BROADCAST_MESSAGE = "S2CC:timer:reset"
S2CC_POSITION_X_VARIABLE_NAME_PREFIX = "S2CC:pos_x_"
S2CC_POSITION_Y_VARIABLE_NAME_PREFIX = "S2CC:pos_y_"
S2CC_SENSOR_PREFIX = "S2CC:sensor_"
S2CC_GETATTRIBUTE_PREFIX = "S2CC:getattribute_"
S2CC_PEN_COLOR_VARIABLE_NAMES = {"h": "S2CC:pen_hue", "s": "S2CC:pen_saturation", "v": "S2CC:pen_value"}
S2CC_PEN_COLOR_DEFAULT_HSV_VALUE = {"h": 0.67, "s": 1.00, "v": 1.00}
S2CC_PEN_COLOR_HELPER_VARIABLE_NAMES = {
    "h_i": "S2CC:_h_i", "f": "S2CC:_f", "p": "S2CC:_p", "q": "S2CC:_q",
    "t": "S2CC:_t", "r": "S2CC:_red", "g": "S2CC:_green", "b": "S2CC:_blue"
}
S2CC_PEN_SIZE_VARIABLE_NAME = "S2CC:pen_size"
S2CC_PEN_SIZE_MULTIPLIER = 3.65
S2CC_PEN_SIZE_DEFAULT_VALUE = (1 * S2CC_PEN_SIZE_MULTIPLIER)
ADD_TIMER_SCRIPT_KEY = "add_timer_script_key"
ADD_TIMER_RESET_SCRIPT_KEY = "add_timer_reset_script_key"
ADD_POSITION_SCRIPT_TO_OBJECTS_KEY = "add_position_script_to_objects_key"
ADD_UPDATE_ATTRIBUTE_SCRIPT_TO_OBJECTS_KEY = "add_update_attribute_script_to_objects_key"
ADD_KEY_PRESSED_SCRIPT_KEY = "add_key_pressed_script_key"
ADD_MOUSE_SPRITE = "add_mouse_sprite"
ADD_PEN_DEFAULT_BEHAVIOR = "add_pen_default_behavior"
ADD_PEN_COLOR_VARIABLES = "add_pen_color_variables"
ADD_PEN_SIZE_VARIABLE = "add_pen_size_variable"
UPDATE_HELPER_VARIABLE_TIMEOUT = 0.04
# TODO: extend whenever new bricks are added
PEN_BRICK_LIST = ["clearPenTrails", "stampCostume", "putPenDown", "putPenUp", "penColor:", "changePenParamBy:",
                  "setPenParamTo:", "changePenSizeBy:", "penSize:", "penShade:", "changePenShadeBy:", "penHue:"]


def verify_resources_of_scratch_object(scratch_object, md5_to_resource_path_map, project_base_path):
    scratch_object_resources = scratch_object.get_sounds() + scratch_object.get_costumes()
    for res_dict in scratch_object_resources:
        assert JsonKeys.SOUND_MD5 in res_dict or JsonKeys.COSTUME_MD5 in res_dict
        md5_file = res_dict[JsonKeys.SOUND_MD5] if JsonKeys.SOUND_NAME in res_dict else res_dict[JsonKeys.COSTUME_MD5]
        resource_md5 = os.path.splitext(md5_file)[0]
        if md5_file not in md5_to_resource_path_map:
            raise ProjectError("Missing resource file at project: {}. Provide resource with md5: {}"
                               .format(project_base_path, resource_md5))

# Returns the count of bricks in blocks (Doesn't count Values, formulas etc.)
def _get_block_count(blocks):
    count = 0
    if isinstance(blocks, list):
        for (i, block) in enumerate(blocks):
            if isinstance(block, list):
                if not isinstance(block[0], list) and block[0] != '()':
                    count += 1
                count += _get_block_count(block)
    return count

def _get_block_position_list(blocks):
    positions_list = []

    def _visit_condition(condition, block_position):
        # brackets are injected in sourcecodemodifier => ignore them for correct offset
        if  condition[0] != '()':
            positions_list.append(block_position)

    def _traverse_condition(condition, block_position):
        _visit_condition(condition, block_position)
        for child_condition in condition:
            if isinstance(child_condition, list):
                _traverse_condition(child_condition, block_position)

    def _visit(block, block_position):
        positions_list.append(block_position)

    def _traverse(blocks):
        assert isinstance(blocks, list)
        for (i, block) in enumerate(blocks):
            assert isinstance(block, list)
            _visit(block, (blocks, i))
            for child in block:
                if isinstance(child, list):
                    #list of bricks
                    if isinstance(child[0], list):
                        _traverse(child)
                    #Conditions
                    else:
                        _traverse_condition(child, (blocks, i))
    _traverse(blocks)
    return positions_list

# TODO: rename
class Object(common.DictAccessWrapper):

    def __init__(self, object_data):
        super(Object, self).__init__(object_data)
        if not self.is_scratch2_project(object_data):
            if not self.is_scratch3_project(object_data):
                raise ObjectError("Input is no valid Scratch object.")
            else:
                self.isScratch3 = True
                return
        for key in (JsonKeys.SOUNDS, JsonKeys.COSTUMES, JsonKeys.SCRIPTS, JsonKeys.LISTS, JsonKeys.VARIABLES, JsonKeys.SCRIPT_COMMENTS):
            if key not in object_data:
                self._dict_object[key] = []
        self.name = self.get_objName()
        self.scripts = [Script(script) for script in self.get_scripts() if Script.is_valid_script_input(script)]
        number_of_ignored_scripts = len(self.get_scripts()) - len(self.scripts)
        if number_of_ignored_scripts > 0:
            _log.debug("Ignored %s scripts", number_of_ignored_scripts)

    def preprocess_object(self, all_sprite_names):
        workaround_info = {
            ADD_TIMER_SCRIPT_KEY: False,
            ADD_TIMER_RESET_SCRIPT_KEY: False,
            ADD_KEY_PRESSED_SCRIPT_KEY: set(),
            ADD_POSITION_SCRIPT_TO_OBJECTS_KEY: set(),
            ADD_UPDATE_ATTRIBUTE_SCRIPT_TO_OBJECTS_KEY: {},
            ADD_MOUSE_SPRITE: False,
            ADD_PEN_DEFAULT_BEHAVIOR: False,
            ADD_PEN_COLOR_VARIABLES: False,
            ADD_PEN_SIZE_VARIABLE: False
        }

        ############################################################################################
        # Comment workaround
        # Before other workarounds, because scratch2 comments uses offsets                         #
        ############################################################################################
        if self._dict_object[JsonKeys.SCRIPT_COMMENTS]:
            # reverse sort, so that adding comments will not invalidate the offset of the next comments
            comments = sorted(self._dict_object[JsonKeys.SCRIPT_COMMENTS], key=itemgetter(5), reverse=True)

            #fix comment offsets if there are bricks outside of scripts
            if len(self.get_scripts()) != len(self.scripts):
                invalid_script_blocks = [None if Script.is_valid_script_input(script) else script[2] for script in self.get_scripts()]
                script = iter(self.scripts)
                block_offset = 0
                for invalid_script_block in invalid_script_blocks:
                    if invalid_script_block:
                        invalid_script_length = _get_block_count(invalid_script_block)
                        # remove comments that are in the invalid script
                        comments = [c for c in comments if not block_offset <= c[5] < block_offset + invalid_script_length]
                        # move all the later comments to the correct offset
                        for comment in comments:
                            if comment[5] > block_offset:
                                comment[5] -= invalid_script_length
                    else:
                        block_offset += 1 + _get_block_count(script.next().blocks)

            position_list = []
            for script in self.scripts:
                position_list.append((script.blocks, 0))
                position_list.extend(_get_block_position_list(script.blocks))

            for (x, y, width, height, isOpen, blockId, text) in comments:
                #Add comments not associated to a block into the 1st script
                if blockId < 0:
                    block_offset = 0
                else:
                    block_offset = blockId
                if block_offset < len(position_list):
                    block_list, offset = position_list[block_offset]
                    block_list.insert(offset, ["note:", text])
                else:
                    _log.warn("Comment with blockId of {} can't be converted.".format(blockId))

        for script in self.scripts:
            script.script_element = ScriptElement.from_raw_block(script.blocks)

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
            if has_timer_block(script.blocks) or 'timer' in script.arguments: workaround_info[ADD_TIMER_SCRIPT_KEY] = True

            script.blocks = replace_timer_blocks(script.blocks)

            # rebuild ScriptElement tree
            script.script_element = ScriptElement.from_raw_block(script.blocks)

        ############################################################################################
        # key pressed workaround
        ############################################################################################

        key_pressed_keys = set()

        def has_key_pressed_block(block_list):
            for block in block_list:
                if isinstance(block, list) and (block[0] == 'keyPressed:' or has_key_pressed_block(block)):
                    return True
            return False

        def replace_key_pressed_blocks(block_list):
            new_block_list = []
            for block in block_list:
                if isinstance(block, list):
                    if block[0] == 'keyPressed:':
                        new_block_list += [["readVariable", S2CC_KEY_VARIABLE_NAME+block[1]]]
                        key_pressed_keys.add((block[1],"keyPressedBrick"))
                    else:
                        new_block_list += [replace_key_pressed_blocks(block)]
                else:
                    new_block_list += [block]
            return new_block_list

        for script in self.scripts:
            if has_key_pressed_block(script.blocks):
                script.blocks = replace_key_pressed_blocks(script.blocks)
                workaround_info[ADD_KEY_PRESSED_SCRIPT_KEY] = key_pressed_keys
                # rebuild ScriptElement tree
                script.script_element = ScriptElement.from_raw_block(script.blocks)

        ############################################################################################
        # distance to object workaround
        ############################################################################################
        def has_distance_to_object_block(block_list, all_sprite_names):
            for block in block_list:
                if isinstance(block, list) \
                        and ((block[0] == 'distanceTo:' and block[1] in (all_sprite_names) + ['_mouse_']) \
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
                        if block[1] == "_mouse_":
                            workaround_info[ADD_MOUSE_SPRITE] = True

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

        ############################################################################################
        # glide to sprite/mouse-pointer/random-position workaround
        ############################################################################################
        def has_glide_to_sprite_script(block_list, all_sprite_names):
            for block in block_list:
                if isinstance(block, list) and (block[0] == 'glideTo:' \
                        and block[-1] in all_sprite_names + ['_mouse_', '_random_'] \
                        or has_glide_to_sprite_script(block, all_sprite_names)):
                    return True
            return False

        def add_glide_to_workaround_script(block_list, positions_needed_for_sprite_names):
            glide_to_workaround_bricks = []
            for block in block_list:
                if isinstance(block, list):
                    if block[0] == 'glideTo:':
                        sprite_name = block[-1]
                        time_in_sec = block[1]
                        random_pos = False
                        if sprite_name == "_random_":
                            random_pos = True
                        elif sprite_name == "_mouse_":
                            workaround_info[ADD_MOUSE_SPRITE] = True
                        else:
                            positions_needed_for_sprite_names.add(sprite_name)

                        if random_pos:
                            left_x, right_x = -STAGE_WIDTH_IN_PIXELS / 2, STAGE_WIDTH_IN_PIXELS / 2
                            lower_y, upper_y = -STAGE_HEIGHT_IN_PIXELS / 2, STAGE_HEIGHT_IN_PIXELS / 2
                            glide_to_workaround_bricks += [[
                                "glideSecs:toX:y:elapsed:from:",
                                time_in_sec,
                                ["randomFrom:to:", left_x, right_x],
                                ["randomFrom:to:", lower_y, upper_y]
                            ]]
                        else:
                            x_pos_var_name = S2CC_POSITION_X_VARIABLE_NAME_PREFIX + sprite_name
                            y_pos_var_name = S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + sprite_name
                            glide_to_workaround_bricks += [[
                                "glideSecs:toX:y:elapsed:from:",
                                time_in_sec,
                                ["readVariable", x_pos_var_name],
                                ["readVariable", y_pos_var_name]
                            ]]
                    else:
                        glide_to_workaround_bricks += [add_glide_to_workaround_script(block, positions_needed_for_sprite_names)]
                else:
                    glide_to_workaround_bricks += [block]
            return glide_to_workaround_bricks

        for script in self.scripts:
            if has_glide_to_sprite_script(script.blocks, all_sprite_names):
                script.blocks = add_glide_to_workaround_script(script.blocks, positions_needed_for_sprite_names)
            script.script_element = ScriptElement.from_raw_block(script.blocks)

        # save which sprites need position tracking from 'distanceTo'- and 'glideTo'-bricks
        workaround_info[ADD_POSITION_SCRIPT_TO_OBJECTS_KEY] = positions_needed_for_sprite_names

        ############################################################################################
        # of-block (getAttribute) workaround
        ############################################################################################
        def replace_getattribute_blocks(block_list, sensor_data_needed_for_sprite_names):
            attribute_name_to_sensor_name_map = {
                "x position": "xpos",
                "y position": "ypos",
                "direction": "heading",
                "costume #": "costumeIndex",
                "backdrop #": "backgroundIndex",
                "backdrop name": "sceneName",
                "size": "scale",
                "costume name": "costumeName",
                # not supported at the moment -> automatically replaced with NoteBrick by converter
                "volume": "volume"
            }
            new_block_list = []
            for block in block_list:
                if not isinstance(block, list):
                    new_block_list += [block]
                    continue

                if block[0] == 'getAttribute:of:':
                    attribute_name, sprite_name = block[1:3]
                    if not isinstance(sprite_name, basestring):
                        new_block_list += [0]
                        continue

                    sprite_name = sprite_name.replace("_stage_", "Stage")
                    sensor_name = attribute_name_to_sensor_name_map.get(attribute_name)

                    # case read variable:
                    if sensor_name is None:
                        variable_name = attribute_name
                        # global variable or local variable of current sprite object
                        if sprite_name in {"Stage", self.name}:
                            new_block_list += [["readVariable", variable_name]]
                            continue
                        # local variable of other sprite
                        else:
                            sensor_name = "readVariable:{}".format(variable_name)

                    # case read sensor of current sprite:
                    if self.name == sprite_name:
                        new_block_list += [[sensor_name]]
                    # case read sensor of other sprite:
                    else:
                        if sprite_name not in sensor_data_needed_for_sprite_names:
                            sensor_data_needed_for_sprite_names[sprite_name] = set()
                        sensor_data_needed_for_sprite_names[sprite_name].add(sensor_name)
                        variable_name = S2CC_GETATTRIBUTE_PREFIX + "{}_{}".format(sprite_name, sensor_name)
                        new_block_list += [["readVariable", variable_name]]
                else:
                    new_block_list += [replace_getattribute_blocks(block, sensor_data_needed_for_sprite_names)]

            return new_block_list

        sensor_data_needed_for_sprite_names = {}
        for script in self.scripts:
            script.blocks = replace_getattribute_blocks(script.blocks, sensor_data_needed_for_sprite_names)
            # parse again ScriptElement tree
            script.script_element = ScriptElement.from_raw_block(script.blocks)
        workaround_info[ADD_UPDATE_ATTRIBUTE_SCRIPT_TO_OBJECTS_KEY] = sensor_data_needed_for_sprite_names

        ############################################################################################
        # pen bricks: change pen [something] by [value] workaround
        ############################################################################################
        def has_pen_brick(block_list):
            for block in block_list:
                if isinstance(block, list) and (block[0] in PEN_BRICK_LIST or has_pen_brick(block)):
                    return True
            return False

        def has_pen_color_param_block(block_list):
            for block in block_list:
                # TODO: remove transparency case as soon as catrobat supports pen transparency change
                if isinstance(block, list) and ((block[0] == 'changePenParamBy:' or block[0] == 'setPenParamTo:')
                and block[1] != 'transparency' or has_pen_color_param_block(block)):
                    return True
            return False

        def has_change_pen_size_block(block_list):
            for block in block_list:
                if isinstance(block, list) and (block[0] == 'changePenSizeBy:'
                or has_change_pen_size_block(block)):
                    return True
            return False

        for script in self.scripts:
            if has_pen_brick(script.blocks):
                workaround_info[ADD_PEN_DEFAULT_BEHAVIOR] = True
            if has_pen_color_param_block(script.blocks):
                workaround_info[ADD_PEN_COLOR_VARIABLES] = True
            if has_change_pen_size_block(script.blocks):
                workaround_info[ADD_PEN_SIZE_VARIABLE] = True
        return workaround_info

    @classmethod
    def is_scratch2_project(cls, object_data):
        return JsonKeys.OBJECT_NAME in object_data
    @classmethod
    def is_scratch3_project(cls, object_data):
        return JsonKeys.TARGETS in object_data

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
        raw_variables_and_sensors_data = filter(lambda var: "target" in var, self.get_children())

        # preprocessing for conversion of visible variables
        self.sprite_variables_map = {}
        sprite_sensors_map = {}
        for info in raw_variables_and_sensors_data:
            assert "target" in info and "param" in info and "visible" in info
            if not info["visible"]: continue
            sprite_name = info["target"]
            if info["cmd"] == "getVar:":
                # case variable
                if sprite_name not in self.sprite_variables_map:
                    self.sprite_variables_map[sprite_name] = []
                self.sprite_variables_map[sprite_name] += [info["param"]]
            else:
                # case sensor
                if sprite_name not in sprite_sensors_map:
                    sprite_sensors_map[sprite_name] = []
                sprite_sensors_map[sprite_name] += [(info["cmd"], info["param"])]

        self.raw_objects = sorted(filter(lambda obj_data: "objName" in obj_data, self.get_children()),
                                  key=lambda obj_data: obj_data.get("indexInLibrary", 0))
        self.objects = [Object(raw_object) for raw_object in [dict_] + self.raw_objects]
        self.resource_names = [self._resource_name_from(raw_resource) for raw_resource in self._raw_resources()]
        self.unique_resource_names = list(set(self.resource_names))
        is_add_timer_script = False
        is_add_timer_reset_script = False
        sprite_name_sprite_mapping = dict(map(lambda obj: (obj.get_objName(), obj), self.objects))
        all_sprite_names = sprite_name_sprite_mapping.keys()
        position_script_to_be_added = set()
        update_attribute_script_to_be_added = {}
        self.listened_keys = set()
        self._has_mouse_position_script = False
        for scratch_object in self.objects:
            workaround_info = scratch_object.preprocess_object(all_sprite_names)
            if workaround_info[ADD_TIMER_SCRIPT_KEY]: is_add_timer_script = True
            if workaround_info[ADD_TIMER_RESET_SCRIPT_KEY]: is_add_timer_reset_script = True
            if workaround_info[ADD_PEN_DEFAULT_BEHAVIOR]:
                self._add_pen_default_behavior_to_object(scratch_object)
            if workaround_info[ADD_PEN_COLOR_VARIABLES]:
                self._add_pen_color_variables_to_object(scratch_object)
                self._add_pen_colo_helper_variables_to_object(scratch_object)
            if workaround_info[ADD_PEN_SIZE_VARIABLE]: self._add_pen_size_variable_to_object(scratch_object)
            if len(workaround_info[ADD_KEY_PRESSED_SCRIPT_KEY]) > 0:
                self.listened_keys.update(workaround_info[ADD_KEY_PRESSED_SCRIPT_KEY])
            position_script_to_be_added |= workaround_info[ADD_POSITION_SCRIPT_TO_OBJECTS_KEY]
            self._has_mouse_position_script |= workaround_info[ADD_MOUSE_SPRITE]

            for sprite_name, sensor_names_set in workaround_info[ADD_UPDATE_ATTRIBUTE_SCRIPT_TO_OBJECTS_KEY].iteritems():
                if sprite_name not in update_attribute_script_to_be_added: update_attribute_script_to_be_added[sprite_name] = set()
                update_attribute_script_to_be_added[sprite_name] |= sensor_names_set
        if is_add_timer_script or is_add_timer_reset_script: self._add_timer_script_to_stage_object()
        if is_add_timer_reset_script: self._add_timer_reset_script_to_stage_object()

        for destination_sprite_name in position_script_to_be_added:
            if destination_sprite_name == "_mouse_": continue
            sprite_object = sprite_name_sprite_mapping[destination_sprite_name]
            assert sprite_object is not None
            self._add_update_position_script_to_object(sprite_object)

        for sprite_name, sensors_info in sprite_sensors_map.iteritems():
            sprite_object = sprite_name_sprite_mapping[sprite_name]
            assert sprite_object is not None
            self._add_sensor_variables_and_update_script_to_object(sprite_object, sensors_info, is_add_timer_script)

        for sprite_name, sensor_names in update_attribute_script_to_be_added.iteritems():
            sprite_object = sprite_name_sprite_mapping[sprite_name]
            assert sprite_object is not None
            self._add_update_attribute_script_to_object(sprite_object, sensor_names)

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
                ["wait:elapsed:from:", UPDATE_HELPER_VARIABLE_TIMEOUT]
            ]]
        ]
        sprite_object.scripts += [Script([0, 0, [[SCRIPT_GREEN_FLAG]] + script_blocks])]

    def _add_update_attribute_script_to_object(self, sprite_object, sensor_names):
        forever_loop_body_blocks = []
        for sensor_name in sensor_names:
            # add variable
            variable_name = S2CC_GETATTRIBUTE_PREFIX + "{}_{}".format(sprite_object.get_objName(), sensor_name)
            global_variables = self.objects[0]._dict_object["variables"]
            global_variables.append({
                "name": variable_name,
                "value": 0,
                "isPersistent": False
            })
            # update variable
            value = [sensor_name] if not sensor_name.startswith("readVariable:") else ["readVariable", sensor_name.split("readVariable:")[1]]
            forever_loop_body_blocks += [["setVar:to:", variable_name, value]]

        forever_loop_body_blocks += [["wait:elapsed:from:", UPDATE_HELPER_VARIABLE_TIMEOUT]]
        sprite_object.scripts += [Script([0, 0, [[SCRIPT_GREEN_FLAG], ["doForever", forever_loop_body_blocks]]])]

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
                ["changeVar:by:", S2CC_TIMER_VARIABLE_NAME, UPDATE_HELPER_VARIABLE_TIMEOUT],
                ["wait:elapsed:from:", UPDATE_HELPER_VARIABLE_TIMEOUT]
            ]]
        ]
        self.objects[0].scripts += [Script([0, 0, [[SCRIPT_GREEN_FLAG]] + script_blocks])]

    def _add_timer_reset_script_to_stage_object(self):
        assert len(self.objects) > 0
        # timer reset script
        script_blocks = [["setVar:to:", S2CC_TIMER_VARIABLE_NAME, 0]]
        self.objects[0].scripts += [Script([0, 0, [[SCRIPT_RECEIVE, S2CC_TIMER_RESET_BROADCAST_MESSAGE]] + script_blocks])]

    def _add_sensor_variables_and_update_script_to_object(self, sprite_object, sensors_info, is_add_timer_script):
        from scratchtocatrobat.converter import converter
        forever_loop_body_blocks = []
        sprite_name = sprite_object.get_objName()
        for command, param in sensors_info:
            if not converter.is_supported_block(command) and command != "timer":
                continue

            if sprite_name not in self.sprite_variables_map:
                self.sprite_variables_map[sprite_name] = []

            stage_object = self.objects[0]
            if command == "timer":
                variable_name = S2CC_TIMER_VARIABLE_NAME
                self.sprite_variables_map[sprite_name] += [variable_name]
                if not is_add_timer_script:
                    self._add_timer_script_to_stage_object()
                continue
            elif command == "answer":
                variable_name = converter._SHARED_GLOBAL_ANSWER_VARIABLE_NAME
                self.sprite_variables_map[sprite_name] += [variable_name]
                stage_object._dict_object["variables"].append({ "name": variable_name, "value": "", "isPersistent": False })
                continue

            variable_name = S2CC_SENSOR_PREFIX + "{}_{}{}".format(sprite_name, command, "_" + param if param else "")
            self.sprite_variables_map[sprite_name] += [variable_name]
            sprite_object._dict_object["variables"].append({ "name": variable_name, "value": 0, "isPersistent": False })
            reporter_block = [command] if param is None else [command, param]
            forever_loop_body_blocks += [["setVar:to:", variable_name, reporter_block]]

        if len(forever_loop_body_blocks) == 0: return
        forever_loop_body_blocks += [["wait:elapsed:from:", UPDATE_HELPER_VARIABLE_TIMEOUT]]
        script_blocks = [["doForever", forever_loop_body_blocks]]
        sprite_object.scripts += [Script([0, 0, [[SCRIPT_GREEN_FLAG]] + script_blocks])]

    def _add_pen_default_behavior_to_object(self, sprite_object):
        default_pen_size = [unicode("penSize:"), 1.0]
        default_pen_color = [unicode("penColor:"), "#0000ff"]
        script_blocks = [default_pen_size, default_pen_color]
        self._add_to_start_script(sprite_object, script_blocks)
        return

    def _add_to_start_script(self, sprite_object, bricks):
        for i, script in enumerate(sprite_object.scripts):
            if script.type == SCRIPT_GREEN_FLAG:
                sprite_object.scripts[i] = Script([0, 0, [[SCRIPT_GREEN_FLAG]] + bricks + script.blocks])
                return
        sprite_object.scripts += [Script([0, 0, [[SCRIPT_GREEN_FLAG]] + bricks])]
        return

    def _add_pen_color_variables_to_object(self, sprite_object):
        for key in S2CC_PEN_COLOR_VARIABLE_NAMES.keys():
            sprite_object._dict_object["variables"].append({
                "name": S2CC_PEN_COLOR_VARIABLE_NAMES[key],
                "value": S2CC_PEN_COLOR_DEFAULT_HSV_VALUE[key],
                "isPersistent": False
            })
        return

    def _add_pen_colo_helper_variables_to_object(self, sprite_object):
        for variable_name in S2CC_PEN_COLOR_HELPER_VARIABLE_NAMES.values():
            sprite_object._dict_object["variables"].append({"name": variable_name, "value": 0, "isPersistent": False})
        return

    def _add_pen_size_variable_to_object(self, sprite_object):
        sprite_object._dict_object["variables"].append(
            {"name": S2CC_PEN_SIZE_VARIABLE_NAME, "value": S2CC_PEN_SIZE_DEFAULT_VALUE, "isPersistent": False}
        )
        return

    def __iter__(self):
        return iter(self.objects)

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
                    raise EnvironmentError("Invalid JSON file. The project's code-file " \
                                           "seems to be a binary file. Project might be very old " \
                                           "Scratch project. Scratch projects lower than 2.0 are " \
                                           "not supported!")
                else:
                    raise EnvironmentError("Invalid JSON file. But the project's " \
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

    def __init__(self, project_base_path, name=None, project_id=None, progress_bar=None, is_local_project=False):
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
        self.project_id = self.get_info().get("projectID") if project_id is None else project_id

        if not is_local_project:
            self.downloadScratch2ProjectResources(project_base_path, progress_bar)

        if not self.project_id:
            self.project_id = "0"
            self.name = name if name is not None else "Untitled"
            self.instructions = self.notes_and_credits = None
            self.automatic_screenshot_image_url = None
        else:

            if name is not None:
                self.name = name
            else:
                self.name = scratchwebapi.getMetaDataEntry(self.project_id, "title")

            # self.name = name if name is not None else scratchwebapi.getMetaDataEntry(self.project_id, "title")

            self.instructions, self.notes_and_credits, self.automatic_screenshot_image_url = \
                scratchwebapi.getMetaDataEntry(self.project_id, "instructions", "description", "image")
            # self.instructions = scratchwebapi.getMetaDataEntry(self.project_id, "instructions")
            # self.notes_and_credits = scratchwebapi.getMetaDataEntry(self.project_id, "description")
            # self.automatic_screenshot_image_url = "{}{}.png".format(scratchwebapi.SCRATCH_PROJECT_IMAGE_BASE_URL, self.project_id)

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
                    listened_keys += [(argument, "listenedKeys") for argument in script.arguments]

        try:
            self.listened_keys.update(listened_keys)
        except AttributeError:
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
        result = []
        for file_path in glob.glob(os.path.join(self.project_base_path, "*.*")):
            md5_resource_filename = common.md5_hash(file_path) + os.path.splitext(file_path)[1]
            if md5_resource_filename not in self.unique_resource_names:
                if os.path.basename(file_path) != _PROJECT_FILE_NAME:
                    result += [(md5_resource_filename, file_path)]
        return map(list, zip(*result))

    def find_all_resource_names_for(self, resource_unique_id):
        resource_names = set()
        for raw_resource in self._raw_resources():
            if resource_unique_id in set([raw_resource.get(JsonKeys.SOUND_MD5), raw_resource.get(JsonKeys.COSTUME_MD5)]):
                resource_names.update([raw_resource[JsonKeys.COSTUME_NAME if JsonKeys.COSTUME_NAME in raw_resource else JsonKeys.SOUND_NAME]])
        return list(resource_names)

    def downloadScratch2ProjectResources(self, target_dir, progress_bar):
        from threading import Thread
        from java.net import SocketTimeoutException, SocketException, UnknownHostException
        from java.io import IOException
        from scratchtocatrobat.tools import common
        from scratchtocatrobat.scratch import scratch
        from scratchtocatrobat.scratch.scratchwebapi import ScratchWebApiError
        from scratchtocatrobat.tools.helpers import ProgressType


        class ResourceDownloadThread(Thread):
            def run(self):
                resource_url = self._kwargs["resource_url"]
                target_dir = self._kwargs["target_dir"]
                md5_file_name = self._kwargs["md5_file_name"]
                progress_bar = self._kwargs["progress_bar"]
                resource_file_path = os.path.join(target_dir, md5_file_name)
                try:
                    common.download_file(resource_url, resource_file_path)
                except (SocketTimeoutException, SocketException, UnknownHostException, IOException) as e:
                    raise ScratchWebApiError("Error with {}: '{}'".format(resource_url, e))
                verify_hash = helpers.md5_of_file(resource_file_path)
                assert verify_hash == os.path.splitext(md5_file_name)[0], "MD5 hash of response data not matching"
                if progress_bar != None:
                    progress_bar.update(ProgressType.DOWNLOAD_MEDIA_FILE)

        # schedule parallel downloads
        unique_resource_names = self.unique_resource_names
        resource_url_template = helpers.config.get("SCRATCH_API", "asset_url_template")
        max_concurrent_downloads = int(helpers.config.get("SCRATCH_API", "http_max_concurrent_downloads"))
        resource_index = 0
        num_total_resources = len(unique_resource_names)
        reference_index = 0
        while resource_index < num_total_resources:
            num_next_resources = min(max_concurrent_downloads, (num_total_resources - resource_index))
            next_resources_end_index = resource_index + num_next_resources
            threads = []
            for index in range(resource_index, next_resources_end_index):
                assert index == reference_index
                reference_index += 1
                md5_file_name = unique_resource_names[index]
                kwargs = { "md5_file_name": md5_file_name,
                           "resource_url": resource_url_template.format(md5_file_name),
                           "target_dir": target_dir,
                           "progress_bar": progress_bar }
                threads.append(ResourceDownloadThread(kwargs=kwargs))
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            resource_index = next_resources_end_index
        assert reference_index == resource_index and reference_index == num_total_resources



class Script(object):

    def __init__(self, script_input):
        if not self.is_valid_script_input(script_input):
            raise ScriptError("Input is no valid Scratch script.")

        self.raw_script = script_input[2]
        self.type = self.raw_script[0][0]

        if self.type not in SCRIPTS:
            raise ScriptError("Unknown Scratch script type: {}".format(self.type))

        script_block, self.blocks = self.raw_script[0], self.raw_script[1:]
        if not self.blocks:
            _log.debug("Empty script: %s", script_input)

        # TODO: add them dynamically!
        for injector in [scriptcodemodifier.ZeroifyEmptyValuesModifier(), scriptcodemodifier.InjectMissingBracketsModifier()]:
            self.blocks = injector.modify(self.blocks)

        self.script_element = ScriptElement.from_raw_block(self.blocks)
        assert isinstance(self.script_element, BlockList)
        self.arguments = script_block[1:]

    @classmethod
    def is_valid_script_input(cls, json_input):
        are_all_positional_values_numbers = all(isinstance(positional_value, (int, float)) for positional_value in json_input[0:2])
        if (isinstance(json_input, list) and len(json_input) == 3 and are_all_positional_values_numbers and isinstance(json_input[2], list)):
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

    def prettyprint(self, verbose=False, indent="", file_=sys.stdout):
        label = "<{}>\n{} {}\n".format(self.__class__.__name__.upper(), indent, self.name) if verbose else self.name
        label = self.name + ("\n" if verbose else "") if isinstance(self, BlockList) else label
        print("{} {}".format(indent, label), file=file_)
        for child in self:
            child.prettyprint(verbose, (indent + "    "), file_=file_)

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
