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
from __future__ import unicode_literals

import itertools
import numbers
import os
import shutil
import types
import zipfile
import re
from codecs import open

from org.catrobat.catroid import ProjectManager
import org.catrobat.catroid.common as catcommon
import org.catrobat.catroid.content as catbase
from org.catrobat.catroid.ui.fragment import SpriteFactory
import org.catrobat.catroid.content.bricks as catbricks
import org.catrobat.catroid.formulaeditor as catformula
import org.catrobat.catroid.formulaeditor.FormulaElement.ElementType as catElementType
import org.catrobat.catroid.io as catio

from scratchtocatrobat.tools import common
from scratchtocatrobat.scratch import scratch
from scratchtocatrobat.tools import logger
from scratchtocatrobat.scratch.scratch import JsonKeys as scratchkeys
from scratchtocatrobat.tools import helpers
from scratchtocatrobat.tools.helpers import ProgressType

from java.awt import Color

import catrobat
import mediaconverter

_DEFAULT_FORMULA_ELEMENT = catformula.FormulaElement(catElementType.NUMBER, str(00001), None)  # @UndefinedVariable (valueOf)

_GENERATED_VARIABLE_PREFIX = helpers.application_info("short_name") + ":"
_SOUND_LENGTH_VARIABLE_NAME_FORMAT = "length_of_{}_in_secs"
_SHARED_GLOBAL_ANSWER_VARIABLE_NAME = _GENERATED_VARIABLE_PREFIX + "global_answer"

_SUPPORTED_IMAGE_EXTENSIONS_BY_CATROBAT = {".gif", ".jpg", ".jpeg", ".png"}
_SUPPORTED_SOUND_EXTENSIONS_BY_CATROBAT = {".mp3", ".wav"}

CATROBAT_DEFAULT_SCENE_NAME = "Scene 1"
UNSUPPORTED_SCRATCH_BLOCK_NOTE_MESSAGE_PREFIX_TEMPLATE = "Missing brick for Scratch identifier: [{}]"
UNSUPPORTED_SCRATCH_FORMULA_BLOCK_NOTE_MESSAGE_PREFIX = "Missing formula element in brick: [{}] for Scratch identifier: [{}]"

log = logger.log


class ConversionError(common.ScratchtobatError):
    pass

class UnmappedBlock(object):

    def __init__(self, sprite, *args):
        self.sprite = sprite
        self.block_and_args = _with_unmapped_blocks_replaced_as_default_formula_value(args)

    def __str__(self):
        return catrobat.simple_name_for(self.block_and_args)

    def to_placeholder_brick(self, held_by_block_name=None):
        return [_placeholder_for_unmapped_blocks_to(*self.block_and_args)] if held_by_block_name is None \
               else [_placeholder_for_unmapped_formula_blocks_to(held_by_block_name, *self.block_and_args)]

def _with_unmapped_blocks_replaced_as_default_formula_value(arguments):
    return [_DEFAULT_FORMULA_ELEMENT if isinstance(argument, UnmappedBlock) else argument for argument in arguments]

def _arguments_string(args):
    return ", ".join(map(catrobat.simple_name_for, args))

def _placeholder_for_unmapped_formula_blocks_to(held_by_block_name, *args):
    held_by_block_name = [held_by_block_name][0]
    return catbricks.NoteBrick(UNSUPPORTED_SCRATCH_FORMULA_BLOCK_NOTE_MESSAGE_PREFIX.format(held_by_block_name, _arguments_string(args)))

def _placeholder_for_unmapped_blocks_to(*args):
    return catbricks.NoteBrick(UNSUPPORTED_SCRATCH_BLOCK_NOTE_MESSAGE_PREFIX_TEMPLATE.format(_arguments_string(args)))

def _key_to_broadcast_message(key_name):
    return "key " + key_name + " pressed"

def _background_look_to_broadcast_message(look_name):
    return "start background scene: " + look_name

def _next_background_look_broadcast_message():
    return "set background to next look"

def _sec_to_msec(duration):
    return duration * 1000

def is_math_function_or_operator(key):
    cls = _ScratchToCatrobat
    all_keys = cls.math_function_block_parameters_mapping.keys() \
             + cls.math_unary_operators_mapping.keys() + cls.math_binary_operators_mapping.keys()
    return key in all_keys

def is_math_operator(key):
    cls = _ScratchToCatrobat
    all_keys = cls.math_unary_operators_mapping.keys() + cls.math_binary_operators_mapping.keys()
    return key in all_keys

# note: for Scratch blocks without mapping placeholder Catrobat bricks will be added
class _ScratchToCatrobat(object):

    math_function_block_parameters_mapping = {
        # math functions
        "abs": catformula.Functions.ABS,
        "sqrt": catformula.Functions.SQRT,
        "sin": catformula.Functions.SIN,
        "cos": catformula.Functions.COS,
        "tan": catformula.Functions.TAN,
        "asin": catformula.Functions.ARCSIN,
        "acos": catformula.Functions.ARCCOS,
        "atan": catformula.Functions.ARCTAN,
        "e^": catformula.Functions.EXP,
        "ln": catformula.Functions.LN,
        "log": catformula.Functions.LOG,
        "rounded": catformula.Functions.ROUND,
        "randomFrom:to:": catformula.Functions.RAND,
        "%": catformula.Functions.MOD,
        "10 ^": None,
        "floor": catformula.Functions.FLOOR,
        "ceiling": catformula.Functions.CEIL,
    }

    math_unary_operators_mapping = {
        "()": None, # this operator is only used internally and not part of Scratch
        "not": catformula.Operators.LOGICAL_NOT,
    }

    math_binary_operators_mapping = {
        "+": catformula.Operators.PLUS,
        "-": catformula.Operators.MINUS,
        "*": catformula.Operators.MULT,
        "/": catformula.Operators.DIVIDE,
        "<": catformula.Operators.SMALLER_THAN,
        "=": catformula.Operators.EQUAL,
        ">": catformula.Operators.GREATER_THAN,
        "&": catformula.Operators.LOGICAL_AND,
        "|": catformula.Operators.LOGICAL_OR,
    }

    user_list_block_parameters_mapping = {
        # user list functions
        "getLine:ofList:": catformula.Functions.LIST_ITEM,
        "lineCountOfList:": catformula.Functions.NUMBER_OF_ITEMS,
        "list:contains:": catformula.Functions.CONTAINS,
    }

    string_function_block_parameters_mapping = {
        # string functions
        "stringLength:": catformula.Functions.LENGTH,
        "letter:of:": catformula.Functions.LETTER,
        "concatenate:with:": catformula.Functions.JOIN
    }

    script_mapping = {
        #
        # Scripts
        #
        scratch.SCRIPT_GREEN_FLAG: catbase.StartScript,
        scratch.SCRIPT_RECEIVE: lambda message: catbase.BroadcastScript(message.lower()), # lower case to prevent case-sensitivity issues in Catrobat...
        scratch.SCRIPT_KEY_PRESSED: lambda key: catbase.BroadcastScript(_key_to_broadcast_message(key)),
        scratch.SCRIPT_SCENE_STARTS: lambda look_name: catbase.BroadcastScript(_background_look_to_broadcast_message(look_name)),
        scratch.SCRIPT_CLICKED: catbase.WhenScript,
        scratch.SCRIPT_CLONED: catbase.WhenClonedScript,
        scratch.SCRIPT_PROC_DEF: catbricks.UserBrick,
        scratch.SCRIPT_SENSOR_GREATER_THAN: None,
        scratch.SCRIPT_WHEN_BACKGROUND_SWITCHES_TO: None
    }

    complete_mapping = dict({
        #
        # Bricks
        #
        "broadcast:": lambda message: catbricks.BroadcastBrick(message.lower()), # lower case to prevent case-sensitivity issues in Catrobat...
        "doBroadcastAndWait": lambda message: catbricks.BroadcastWaitBrick(message.lower()), # lower case to prevent case-sensitivity issues in Catrobat...
        "wait:elapsed:from:": lambda duration: catbricks.WaitBrick(catrobat.create_formula_with_value(duration)),

        # control
        "doForever": catbricks.ForeverBrick,
        "doIf": None,
        "doIfElse": None,
        "doRepeat": catbricks.RepeatBrick,
        "doUntil": catbricks.RepeatUntilBrick,
        "doWaitUntil": lambda condition: catbricks.WaitUntilBrick(catrobat.create_formula_with_value(condition)),
        "stopScripts": lambda subject: catbricks.StopScriptBrick(["this script", "all", "other scripts in sprite"].index(subject) if subject != "other scripts in stage" else 2),

        # motion
        "turnRight:": catbricks.TurnRightBrick,
        "turnLeft:": catbricks.TurnLeftBrick,
        "heading:": catbricks.PointInDirectionBrick,
        "forward:": catbricks.MoveNStepsBrick,
        "pointTowards:": catbricks.PointToBrick,
        "gotoX:y:": catbricks.PlaceAtBrick,
        "gotoSpriteOrMouse:": catbricks.GoToBrick,
        "glideSecs:toX:y:elapsed:from:": lambda duration, x_pos, y_pos: catbricks.GlideToBrick(x_pos, y_pos, _sec_to_msec(duration) if isinstance(duration, numbers.Number) else duration),
        "xpos:": catbricks.SetXBrick,
        "ypos:": catbricks.SetYBrick,
        "bounceOffEdge": catbricks.IfOnEdgeBounceBrick,
        "changeXposBy:": catbricks.ChangeXByNBrick,
        "changeYposBy:": catbricks.ChangeYByNBrick,
        "setRotationStyle": catbricks.SetRotationStyleBrick,

        # variables
        "setVar:to:": lambda *args: _create_variable_brick(*itertools.chain(args, [catbricks.SetVariableBrick])),
        "changeVar:by:": lambda *args: _create_variable_brick(*itertools.chain(args, [catbricks.ChangeVariableBrick])),
        "readVariable": lambda variable_name: _variable_for(variable_name),
        "showVariable:": catbricks.ShowTextBrick,
        "hideVariable:": catbricks.HideTextBrick,

        # formula lists
        "append:toList:": catbricks.AddItemToUserListBrick,
        "insert:at:ofList:": catbricks.InsertItemIntoUserListBrick,
        "deleteLine:ofList:": catbricks.DeleteItemOfUserListBrick,
        "setLine:ofList:to:": catbricks.ReplaceItemInUserListBrick,
        #"showList:": catbricks.*, # TODO: implement this as soon as Catrobat supports this...
        #"hideList:": catbricks.*, # TODO: implement this as soon as Catrobat supports this...

        # looks
        "lookLike:": catbricks.SetLookBrick,
        "nextCostume": catbricks.NextLookBrick,
        "startScene": catbricks.SetBackgroundBrick,
        "startSceneAndWait": catbricks.SetBackgroundAndWaitBrick,
        "nextScene": catbricks.NextLookBrick,  # only allowed in scene object so same as nextLook

        # video
        "setVideoState": lambda status: [
            catbricks.ChooseCameraBrick(1),                       # use front camera by default!
            catbricks.CameraBrick(int(status.lower() != 'off'))
        ],

        "changeGraphicEffect:by:": None,
        "setGraphicEffect:to:": lambda effect_type, value:
            catbricks.SetBrightnessBrick(value) if effect_type == 'brightness' else
            catbricks.SetTransparencyBrick(value) if effect_type == 'ghost' else
            _placeholder_for_unmapped_blocks_to("setGraphicEffect:to:", effect_type, value),
        "filterReset": catbricks.ClearGraphicEffectBrick,
        "changeSizeBy:": catbricks.ChangeSizeByNBrick,
        "setSizeTo:": catbricks.SetSizeToBrick,
        "show": catbricks.ShowBrick,
        "hide": catbricks.HideBrick,
        "comeToFront": catbricks.ComeToFrontBrick,
        "goBackByLayers:": catbricks.GoNStepsBackBrick,

        # sound
        "playSound:": catbricks.PlaySoundBrick,
        "doPlaySoundAndWait": catbricks.PlaySoundAndWaitBrick,
        "stopAllSounds": catbricks.StopAllSoundsBrick,
        "changeVolumeBy:": catbricks.ChangeVolumeByNBrick,
        "setVolumeTo:": catbricks.SetVolumeToBrick,

        # bubble bricks
        "say:duration:elapsed:from:": catbricks.SayForBubbleBrick,
        "say:": catbricks.SayBubbleBrick,
        "think:duration:elapsed:from:": catbricks.ThinkForBubbleBrick,
        "think:": catbricks.ThinkBubbleBrick,
        "doAsk": catbricks.AskBrick,
        "answer": None,

        # sprite values
        "xpos": catformula.Sensors.OBJECT_X,
        "ypos": catformula.Sensors.OBJECT_Y,
        "heading": catformula.Sensors.OBJECT_ROTATION,
        "scale": catformula.Sensors.OBJECT_SIZE,

        # sensors
        "mousePressed": catformula.Sensors.FINGER_TOUCHED,
        "mouseX": catformula.Sensors.FINGER_X,
        "mouseY": catformula.Sensors.FINGER_Y,
        "timeAndDate": None,
        "touching:": None,

        # clone
        "createCloneOf": catbricks.CloneBrick,
        "deleteClone": catbricks.DeleteThisCloneBrick,

        # custom block (user-defined)
        "call": None,
        "getParam": lambda variable_name, _: _variable_for(variable_name),

        # pen bricks
        "putPenDown": catbricks.PenDownBrick,
        "putPenUp": catbricks.PenUpBrick,
        "stampCostume": catbricks.StampBrick,
        "clearPenTrails": catbricks.ClearBackgroundBrick,
        "penColor:": catbricks.SetPenColorBrick,
        "penSize:": catbricks.SetPenSizeBrick,
        "setPenHueTo:": None,
        #"changePenSizeBy:": None,
        #"changePenHueBy:": None,

        #name and number
        "sceneName": catformula.Sensors.OBJECT_BACKGROUND_NAME,
        "backgroundIndex": catformula.Sensors.OBJECT_BACKGROUND_NUMBER,
        "costumeIndex": catformula.Sensors.OBJECT_LOOK_NUMBER,

        # WORKAROUND: using ROUND for Catrobat float => Scratch int
        "soundLevel": lambda *_args: catrobat.formula_element_for(catformula.Functions.ROUND,
                                       arguments=[catrobat.formula_element_for(catformula.Sensors.LOUDNESS)]),  # @UndefinedVariable
    }.items() + math_function_block_parameters_mapping.items() \
              + math_unary_operators_mapping.items() + math_binary_operators_mapping.items() \
              + user_list_block_parameters_mapping.items() \
              + string_function_block_parameters_mapping.items())

    @classmethod
    def catrobat_script_class_for(cls, scratch_block_name):
        assert isinstance(scratch_block_name, (str, unicode))
        catrobat_script = cls.script_mapping.get(scratch_block_name)
        return catrobat_script

    @classmethod
    def catrobat_brick_class_for(cls, scratch_block_name):
        assert isinstance(scratch_block_name, (str, unicode))
        catrobat_brick = cls.complete_mapping.get(scratch_block_name)
        if isinstance(catrobat_brick, types.LambdaType):
            catrobat_brick.__name__ = scratch_block_name + "-lambda"
        return catrobat_brick

    @classmethod
    def create_script(cls, scratch_script_name, arguments, catrobat_project, sprite, context=None):
        if scratch_script_name not in scratch.SCRIPTS:
            assert False, "Missing script mapping for: " + scratch_script_name
        catrobat_script = cls.catrobat_script_class_for(scratch_script_name)
        # TODO: register handler!! -> _ScriptBlocksConversionTraverser
        if scratch_script_name == scratch.SCRIPT_SENSOR_GREATER_THAN:
            formula = _create_modified_formula_brick(arguments[0], arguments[1], catrobat_project, sprite)
            when_cond_brick = catbricks.WhenConditionBrick()
            when_cond_brick.addAllowedBrickField(catbricks.Brick.BrickField.IF_CONDITION) #@UndefinedVariable
            when_cond_brick.setFormulaWithBrickField(catbricks.Brick.BrickField.IF_CONDITION, formula) #@UndefinedVariable
            my_script = catbase.WhenConditionScript(when_cond_brick)
            my_script.formulaMap = when_cond_brick.formulaMap
            return my_script

        if scratch_script_name == scratch.SCRIPT_WHEN_BACKGROUND_SWITCHES_TO:
            background = catrobat.background_sprite_of(catrobat_project.getDefaultScene())
            background = sprite if background is None else background
            assert catrobat.is_background_sprite(background)
            for look in background.getLookDataList():
                if arguments[0] == look.getLookName():
                    background_changes_script = catbase.WhenBackgroundChangesScript()
                    background_changes_script.setLook(look)
                    return background_changes_script

        if scratch_script_name != scratch.SCRIPT_PROC_DEF:
            return catrobat_script(*arguments)

        # ["procDef", "Function1 %n string: %s", ["number1", "string1"], [1, ""], true]
        assert len(arguments) == 4
        assert catrobat_script is catbricks.UserBrick

        scratch_function_header = arguments[0]
        param_labels = arguments[1]
        param_values = arguments[2]
        assert param_labels == context.user_script_declared_labels_map[scratch_function_header]
        return _create_user_brick(context, scratch_function_header, param_values, declare=True)

def _create_modified_formula_brick(sensor_type, unconverted_formula, catrobat_project, sprite):

    def _create_catrobat_sprite_stub(name=None):
        sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, "WCTDummy" if name is None else name)
        looks = sprite.getLookDataList()
        for lookname in ["look1", "look2", "look3"]:
            looks.add(catrobat.create_lookdata(lookname, None))
        return sprite

    formula_left_child = None
    formula_right_child = None

    if sensor_type == 'timer':
        formula_left_child = catformula.FormulaElement(catElementType.USER_VARIABLE, None, None)
        formula_left_child.value = scratch.S2CC_TIMER_VARIABLE_NAME

    elif sensor_type == 'loudness':
        formula_left_child = catformula.FormulaElement(catElementType.SENSOR, None, None)
        formula_left_child.value = str(catformula.Sensors.LOUDNESS)

    else:
        #TODO: Implement if ready. Other sensor types (up to now only video motion) not supported.
        raise common.ScratchtobatError("Unsupported sensor type '{}'".format(sensor_type))

    if isinstance(unconverted_formula, int):
        formula_right_child = catformula.FormulaElement(catElementType.NUMBER, None, None)
        formula_right_child.value = str(unconverted_formula)

    else:
        test_project = catbase.Project(None, "__wct_test_project__")
        test_scene = catbase.Scene(None, "Scene 1", test_project)
        test_project.sceneList.add(test_scene)
        tmp_block_conv = _ScratchObjectConverter(test_project, None)
        dummy = _create_catrobat_sprite_stub()
        [formula_right_child] = tmp_block_conv._catrobat_bricks_from(unconverted_formula, dummy)
        assert isinstance(formula_right_child, catformula.FormulaElement)

    traverser = _BlocksConversionTraverser(sprite, catrobat_project)
    return catformula.Formula(traverser._converted_helper_brick_or_formula_element([formula_left_child, formula_right_child], ">"))

def _create_user_brick(context, scratch_function_header, param_values, declare=False):
    param_labels = context.user_script_declared_labels_map[scratch_function_header]
    assert context is not None and isinstance(context, SpriteContext)
    assert not param_labels or len(param_labels) == len(param_values)
    is_user_script_defined = scratch_function_header not in context.user_script_definition_brick_map

    if declare:
        if scratch_function_header in context.user_script_declared_map:
            raise common.ScratchtobatError("Encountered duplicate procDef having signature={}"
                                           .format(scratch_function_header))

        context.user_script_declared_map.add(scratch_function_header)

    # filter all % characters
    filtered_scratch_function_header = scratch_function_header.replace("\\%", "")
    num_of_params = filtered_scratch_function_header.count("%")
    function_header_parts = filtered_scratch_function_header.split()
    num_function_header_parts = len(function_header_parts)
    expected_param_types = [None] * num_of_params

    if not is_user_script_defined:
        user_script_definition_brick = context.user_script_definition_brick_map[scratch_function_header]
        expected_param_types = context.user_script_params_map[scratch_function_header]
    else:
        user_script_definition_brick = catbricks.UserScriptDefinitionBrick()

    assert len(param_values) == num_of_params
    assert len(expected_param_types) == num_of_params
    assert isinstance(user_script_definition_brick, catbricks.UserScriptDefinitionBrick)

    user_brick = catbricks.UserBrick(user_script_definition_brick)
    user_script_definition_brick_elements_list = user_script_definition_brick.getUserScriptDefinitionBrickElements()
    user_brick_parameters_list = user_brick.getUserBrickParameters()

    assert is_user_script_defined \
           or len(user_script_definition_brick_elements_list) == num_function_header_parts

    param_types = []
    param_index = 0

    # example: filtered_scratch_function_header = "label0 %n %s %b label1"
    #          param_default_values = ["number1", "string1", "boolean1"]
    for element_index, function_header_part in enumerate(function_header_parts):
        if not function_header_part.startswith('%'):
            if not is_user_script_defined:
                continue

            # TODO: decide when line-breaks are useful...
            user_script_definition_brick_element = catbricks.UserScriptDefinitionBrickElement()
            user_script_definition_brick_element.setIsText()
            user_script_definition_brick_element.setText(function_header_part)
            user_script_definition_brick_elements_list.add(user_script_definition_brick_element)
            continue

        assert len(function_header_part) == 2
        assert function_header_part in {'%n', '%s', '%b'}
        assert not expected_param_types[param_index] or expected_param_types[param_index] == function_header_part

        if is_user_script_defined:
            user_script_definition_brick_element = catbricks.UserScriptDefinitionBrickElement()
            user_script_definition_brick_element.setIsVariable()
            user_script_definition_brick_elements_list.add(user_script_definition_brick_element)
        else:
            user_script_definition_brick_element = user_script_definition_brick_elements_list.get(element_index)

        user_script_definition_brick_element.setText(param_labels[param_index])
        param_types += [function_header_part]
        param_value = param_values[param_index]
        if not isinstance(param_value, catformula.FormulaElement):
            param_value = int(param_value) if function_header_part in {'%n', '%b'} else str(param_value)
        param_value_formula = catrobat.create_formula_with_value(param_value)

        user_brick_parameter = catbricks.UserBrickParameter(param_value_formula)
        user_brick_parameter.setParent(user_brick)
        user_brick_parameter.setElement(user_script_definition_brick_element)
        user_brick_parameters_list.add(user_brick_parameter)
        param_index += 1

    if is_user_script_defined:
        context.user_script_definition_brick_map[scratch_function_header] = user_script_definition_brick
        context.user_script_params_map[scratch_function_header] = param_types

    return user_brick

def _create_variable_brick(value, user_variable, Class):
    assert Class in set([catbricks.SetVariableBrick, catbricks.ChangeVariableBrick])
    assert isinstance(user_variable, catformula.UserVariable)
    return Class(catrobat.create_formula_with_value(value), user_variable)

def _variable_for(variable_name):
    return catformula.FormulaElement(catElementType.USER_VARIABLE, variable_name, None)  # @UndefinedVariable

def _get_or_create_shared_global_answer_variable(project, data_container, script_context):
    shared_global_answer_user_variable = data_container.getUserVariable(_SHARED_GLOBAL_ANSWER_VARIABLE_NAME, None)
    if shared_global_answer_user_variable is None:
        assert(_is_generated(_SHARED_GLOBAL_ANSWER_VARIABLE_NAME))
        catrobat.add_user_variable(project, _SHARED_GLOBAL_ANSWER_VARIABLE_NAME, None, None)
        shared_global_answer_user_variable = data_container.getUserVariable(_SHARED_GLOBAL_ANSWER_VARIABLE_NAME, None)
        script_context.sprite_context.created_shared_global_answer_user_variable = True

    assert shared_global_answer_user_variable is not None \
    and shared_global_answer_user_variable.getName() == _SHARED_GLOBAL_ANSWER_VARIABLE_NAME, \
    "variable: %s" % (_SHARED_GLOBAL_ANSWER_VARIABLE_NAME)
    return shared_global_answer_user_variable

# TODO: refactor _key_* functions to be used just once
def _key_image_path_for(key):
    key_images_path = os.path.join(common.get_project_base_path(), 'resources', 'images', 'keys')
    for key_filename in os.listdir(key_images_path):
        basename, _ = os.path.splitext(key_filename)
        if basename.lower().endswith("_" + "_".join(key.split())):
            return os.path.join(key_images_path, key_filename)
    assert False, "Key '%s' not found in %s" % (key, os.listdir(key_images_path))


# TODO:  refactor _key_* functions to be used just once
def _key_filename_for(key):
    assert key is not None
    key_path = _key_image_path_for(key)
    # TODO: extract method, already used once
    return common.md5_hash(key_path) + "_" + _key_to_broadcast_message(key) + os.path.splitext(key_path)[1]


def generated_variable_name(variable_name):
    return _GENERATED_VARIABLE_PREFIX + variable_name


def _sound_length_variable_name_for(resource_name):
    return generated_variable_name(_SOUND_LENGTH_VARIABLE_NAME_FORMAT.format(resource_name))


def _is_generated(variable_name):
    return variable_name.startswith(_GENERATED_VARIABLE_PREFIX)

class Context(object):
    def __init__(self):
        self._sprite_contexts = []
        self.upcoming_sprites = {}

    def add_sprite_context(self, sprite_context):
        assert isinstance(sprite_context, SpriteContext)
        self._sprite_contexts += [sprite_context]

    @property
    def sprite_contexts(self):
        return self._sprite_contexts

class SpriteContext(object):
    def __init__(self, name=None, user_script_declared_labels_map={}):
        self.name = name
        self.created_shared_global_answer_user_variable = False
        self.user_script_definition_brick_map = {}
        self.user_script_declared_map = set()
        self.user_script_declared_labels_map = user_script_declared_labels_map
        self.user_script_params_map = {}
        self.context = None

class ScriptContext(object):
    def __init__(self, sprite_context=None):
        self.sprite_context = sprite_context if sprite_context is not None else SpriteContext()

def converted(scratch_project, progress_bar=None, context=None):
    return Converter.converted_project_for(scratch_project, progress_bar, context)


class Converter(object):

    def __init__(self, scratch_project):
        self.visible_var_X = -220
        self.visible_var_Y = 170
        self.visible_var_X_init = -220
        self.visible_var_Y_init = 170
        self.visible_var_position_step_Y = 40
        self.visible_var_position_step_X = 80
        self.visible_var_position_threshold_Y = -20
        self.visible_var_position_threshold_X = 220
        self.scratch_project = scratch_project

    @classmethod
    def converted_project_for(cls, scratch_project, progress_bar=None, context=None):
        converter = Converter(scratch_project)
        catrobat_project = converter._converted_catrobat_program(progress_bar, context)
        assert catrobat.is_background_sprite(catrobat_project.getDefaultScene().getSpriteList().get(0))
        return ConvertedProject(catrobat_project, scratch_project)

    def _add_bricks_for_visible_variables(self, catrobat_scene):
        scratch_project = self.scratch_project
        brick_list = []
        for var in scratch_project._var_to_visibility_map:
            if(scratch_project._var_to_visibility_map.get(var)):
                actual_var = _ScratchObjectConverter._catrobat_scene.getDataContainer().getUserVariable(var, None)
                show_variable_brick = catbricks.ShowTextBrick(self.visible_var_X, self.visible_var_Y)
                show_variable_brick.setUserVariableName(var)
                show_variable_brick.setUserVariable(actual_var)
                brick_list.append(show_variable_brick)
            self.visible_var_Y -= self.visible_var_position_step_Y
            if self.visible_var_Y <= self.visible_var_position_threshold_Y:
                self.visible_var_Y = self.visible_var_Y_init
                self.visible_var_X += self.visible_var_position_step_X
                if self.visible_var_X >= self.visible_var_position_threshold_X:
                    log.info("Too many visible variables")
                    break
        when_started_script = catbase.StartScript()
        when_started_script.getBrickList().addAll(brick_list)
        catrobat_scene.getSpriteList().get(0).addScript(when_started_script)
        return

    def _converted_catrobat_program(self, progress_bar=None, context=None):
        scratch_project = self.scratch_project
        _catr_project = catbase.Project(None, scratch_project.name)
        _catr_scene = catbase.Scene(None, CATROBAT_DEFAULT_SCENE_NAME, _catr_project)
        _catr_project.sceneList.add(_catr_scene)
        ProjectManager.getInstance().setProject(_catr_project)

        self._scratch_object_converter = _ScratchObjectConverter(_catr_project, scratch_project,
                                                                 progress_bar, context)
        self._add_global_user_lists_to(_catr_scene)
        self._add_converted_sprites_to(_catr_scene)
        self._add_key_sprites_to(_catr_scene, self.scratch_project.listened_keys)
        self._update_xml_header(_catr_project.getXmlHeader(), scratch_project.project_id,
                                scratch_project.name, scratch_project.instructions,
                                scratch_project.notes_and_credits)
        self._add_bricks_for_visible_variables(_catr_scene)
        return _catr_project

    def _add_global_user_lists_to(self, catrobat_scene):
        if self.scratch_project.global_user_lists is None:
            return

        for global_user_list in self.scratch_project.global_user_lists:
            # TODO: use "visible" as soon as show/hide-formula-list-bricks are available in Catrobat => global_formula_list["visible"]
            # TODO: use "isPersistent" as soon as Catrobat supports this => global_formula_list["isPersistent"]
            data_container = catrobat_scene.getDataContainer()
            data_container.addProjectUserList(global_user_list["listName"])

    def _add_converted_sprites_to(self, catrobat_scene):
        for scratch_object in self.scratch_project.objects:
            catr_sprite = self._scratch_object_converter(scratch_object)
            catrobat_scene.addSprite(catr_sprite)

    @staticmethod
    def _place_key_brick(key, x_pos, y_pos, catrobat_scene):
        key_filename = _key_filename_for(key)
        key_message = _key_to_broadcast_message(key)
        key_sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, key_message)
        key_look = catcommon.LookData()
        key_look.setLookName(key_message)
        key_look.setLookFilename(key_filename)
        key_sprite.getLookDataList().add(key_look)
        when_started_script = catbase.StartScript()
        set_look_brick = catbricks.SetLookBrick()
        set_look_brick.setLook(key_look)
        place_at_brick = catbricks.PlaceAtBrick(x_pos, y_pos)
        bricks = [place_at_brick, set_look_brick, catbricks.SetSizeToBrick(33)]
        when_started_script.getBrickList().addAll(bricks)
        key_sprite.addScript(when_started_script)
        when_tapped_script = catbase.WhenScript()
        when_tapped_script.addBrick(catbricks.BroadcastBrick(key_message))
        key_sprite.addScript(when_tapped_script)
        catrobat_scene.addSprite(key_sprite)

    # TODO: make it more explicit that this depends on the conversion code for "whenKeyPressed" Scratch block
    @staticmethod
    def _add_key_sprites_to(catrobat_scene, listened_keys):
        y_offset = -20
        x_offset = -20
        space_letters_width_offset = 4
        letters_per_row = 12
        space_exists = False
        if "space" in listened_keys:
            space_exists = True
            listened_keys.remove("space")
        for idx, key in enumerate(listened_keys):
            if space_exists and idx > 3:
                idx = idx + space_letters_width_offset
            width_pos = idx % letters_per_row
            height_pos = int(idx / letters_per_row) + 1
            y_pos = -(scratch.STAGE_HEIGHT_IN_PIXELS / 2) + y_offset + 40 * height_pos
            x_pos = -(scratch.STAGE_WIDTH_IN_PIXELS / 2) + x_offset + 40 * (width_pos + 1)
            Converter._place_key_brick(key, x_pos, y_pos,catrobat_scene)
        if space_exists:
            listened_keys.add("space")
            y_pos = -(scratch.STAGE_HEIGHT_IN_PIXELS / 2) + y_offset + 40
            x_pos = 0
            Converter._place_key_brick("space", x_pos, y_pos, catrobat_scene)

    @staticmethod
    def _update_xml_header(xml_header, scratch_project_id, program_name, scratch_project_instructions,
                           scratch_project_notes_and_credits):
        xml_header.setVirtualScreenHeight(scratch.STAGE_HEIGHT_IN_PIXELS)
        xml_header.setVirtualScreenWidth(scratch.STAGE_WIDTH_IN_PIXELS)
        xml_header.setApplicationBuildName(helpers.application_info("build_name"))
        nums = re.findall(r'\d+', helpers.application_info("build_number"))
        build_number = int(nums[0]) if len(nums) > 0 else 0
        xml_header.setApplicationBuildNumber(build_number)
        xml_header.setApplicationName(helpers.application_info("name"))
        xml_header.setApplicationVersion(helpers.application_info("version"))
        xml_header.setProgramName('%s' % program_name) # NOTE: needed to workaround unicode issue!
        xml_header.setCatrobatLanguageVersion(catrobat.CATROBAT_LANGUAGE_VERSION)
        xml_header.setDeviceName(helpers.scratch_info("device_name"))
        xml_header.setPlatform(helpers.scratch_info("platform"))
        xml_header.setPlatformVersion(float(helpers.scratch_info("platform_version")))
        xml_header.setScreenMode(catcommon.ScreenModes.STRETCH)
        xml_header.mediaLicense = helpers.catrobat_info("media_license_url")
        xml_header.programLicense = helpers.catrobat_info("program_license_url")
        assert scratch_project_id is not None

        #-------------------------------------------------------------------------------------------
        # ATTENTION: *** CATROBAT REMIX SPECIFICATION REQUIREMENT ***
        #-------------------------------------------------------------------------------------------
        #       Keep in mind that the remixOf-field is used by Catroweb's web application only!!!
        #       Once new Catrobat programs get uploaded, Catroweb automatically updates
        #       the remixOf-field and sets the program as being remixed!
        #       In order to do so, Catroweb takes the value from the url-field and assigns it to
        #       the remixOf-field.
        #
        #       With that said, the only correct way to set a remix-URL *before* uploading a
        #       Catrobat program is to insert it into the url-field!
        #       That's why the url of the Scratch program is assigned to the url-field here.
        #-------------------------------------------------------------------------------------------
        xml_header.setRemixParentsUrlString(helpers.config.get("SCRATCH_API", "project_base_url") + scratch_project_id)
        # TODO: @Christian: use setUrl() instead after next catroid-class-hierarchy update!!!
        #       -> setUrl() will be available soon

        sep_line = "\n" + "-" * 40 + "\n"
        description = sep_line
        try:
            if scratch_project_instructions is not None:
                description += "Instructions:\n" + scratch_project_instructions + sep_line
        except:
            # TODO: FIX ASCII issue!!
            pass

        try:
            if scratch_project_notes_and_credits is not None:
                description += "Description:\n" + scratch_project_notes_and_credits + sep_line
        except:
            # TODO: FIX ASCII issue!!
            pass

        description += "\nMade with {} version {}.\nOriginal Scratch project => {}".format( \
                         helpers.application_info("name"), \
                         helpers.application_info("version"), \
                         xml_header.getRemixParentsUrlString())
        xml_header.setDescription(description)

class _ScratchObjectConverter(object):
    _catrobat_project = None
    _scratch_project = None

    def __init__(self, catrobat_project, scratch_project, progress_bar=None, context=None):
        # TODO: refactor static
        _ScratchObjectConverter._catrobat_project = catrobat_project
        _ScratchObjectConverter._catrobat_scene = catrobat_project.getDefaultScene()
        _ScratchObjectConverter._scratch_project = scratch_project
        self._progress_bar = progress_bar
        self._context = context

    def __call__(self, scratch_object):
        return self._catrobat_sprite_from(scratch_object)

    def _catrobat_sprite_from(self, scratch_object):
        if not isinstance(scratch_object, scratch.Object):
            raise common.ScratchtobatError("Input must be of type={}, but is={}".format(scratch.Object, type(scratch_object)))
        sprite_name = scratch_object.name
        scratch_user_scripts = filter(lambda s: s.type == scratch.SCRIPT_PROC_DEF, scratch_object.scripts)
        scratch_user_script_declared_labels_map = dict(map(lambda s: (s.arguments[0], s.arguments[1]), scratch_user_scripts))
        sprite_context = SpriteContext(sprite_name, scratch_user_script_declared_labels_map)

        sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, sprite_name)

        if self._context is not None:
            sprite_context.context = self._context
            if sprite_name in self._context.upcoming_sprites:
                sprite = self._context.upcoming_sprites[sprite_name]

        assert sprite_name == sprite.getName()
        log.info('-'*80)
        log.info("Converting Sprite: '%s'", sprite.getName())
        log.info('-'*80)

        # rename if sprite is background
        if scratch_object.is_stage():
            catrobat.set_as_background(sprite)
            sprite_context.name = sprite.getName()

        # looks and sounds has to added first because of cross-validations
        sprite_looks = sprite.getLookDataList()
        costume_resolution = None
        for scratch_costume in scratch_object.get_costumes():
            current_costume_resolution = scratch_costume.get(scratchkeys.COSTUME_RESOLUTION)
            if not costume_resolution:
                costume_resolution = current_costume_resolution
            elif current_costume_resolution != costume_resolution:
                log.warning("Costume resolution not same for all costumes")
            sprite_looks.add(self._catrobat_look_from(scratch_costume))

        sprite_sounds = sprite.getSoundList()
        for scratch_sound in scratch_object.get_sounds():
            sprite_sounds.add(self._catrobat_sound_from(scratch_sound))

        if not scratch_object.is_stage() and scratch_object.get_lists() is not None:
            catr_data_container = self._catrobat_scene.getDataContainer()
            for user_list_data in scratch_object.get_lists():
                assert len(user_list_data["listName"]) > 0
                catr_data_container.addSpriteUserListToSprite(sprite, user_list_data["listName"])
                # TODO: check if user list has been added...

        for scratch_variable in scratch_object.get_variables():
            user_variable = catrobat.add_user_variable(
                    self._catrobat_project,
                    scratch_variable["name"],
                    sprite=sprite,
                    sprite_name=sprite.getName() if not scratch_object.is_stage() else None
            )
            assert user_variable is not None
            user_variable = self._catrobat_scene.getDataContainer().getUserVariable(scratch_variable["name"], sprite)
            assert user_variable is not None

        for scratch_script in scratch_object.scripts:
            cat_instance = self._catrobat_script_from(scratch_script, sprite, self.__class__._catrobat_project,
                                                      sprite_context)
            if not isinstance(cat_instance, catbricks.UserBrick):
                assert isinstance(cat_instance, catbase.Script)
                sprite.addScript(cat_instance)
            else:
                sprite.addUserBrick(cat_instance)

            if self._progress_bar != None:
                self._progress_bar.update(ProgressType.CONVERT_SCRIPT)

        if self._context is not None:
            self._context.add_sprite_context(sprite_context)

        try:
            self._add_default_behaviour_to(sprite, sprite_context, self._catrobat_scene,
                                           self._catrobat_project, scratch_object,
                                           self._scratch_project, costume_resolution)
        except:
            log.error("Cannot add default behaviour to sprite object {}".format(sprite_name))

        log.info('')
        return sprite

    @staticmethod
    def _catrobat_look_from(scratch_costume):
        if not scratch_costume or not (isinstance(scratch_costume, dict) and all(_ in scratch_costume for _ in (scratchkeys.COSTUME_MD5, scratchkeys.COSTUME_NAME))):
            raise common.ScratchtobatError("Wrong input, must be costume dict: {}".format(scratch_costume))
        look = catcommon.LookData()

        assert scratchkeys.COSTUME_NAME in scratch_costume
        costume_name = scratch_costume[scratchkeys.COSTUME_NAME]
        look.setLookName(costume_name)

        assert scratchkeys.COSTUME_MD5 in scratch_costume
        costume_md5_filename = scratch_costume[scratchkeys.COSTUME_MD5]
        costume_resource_name = scratch_costume[scratchkeys.COSTUME_NAME]
        look.setLookFilename(mediaconverter.catrobat_resource_file_name_for(costume_md5_filename, costume_resource_name))
        return look

    @staticmethod
    def _catrobat_sound_from(scratch_sound):
        soundinfo = catcommon.SoundInfo()

        assert scratchkeys.SOUND_NAME in scratch_sound
        sound_name = scratch_sound[scratchkeys.SOUND_NAME]
        soundinfo.setTitle(sound_name)

        assert scratchkeys.SOUND_MD5 in scratch_sound
        sound_md5_filename = scratch_sound[scratchkeys.SOUND_MD5]
        sound_resource_name = scratch_sound[scratchkeys.SOUND_NAME]
        soundinfo.setSoundFileName(mediaconverter.catrobat_resource_file_name_for(sound_md5_filename, sound_resource_name))
        return soundinfo

    @staticmethod
    def _add_default_behaviour_to(sprite, sprite_context, catrobat_scene, catrobat_project,
                                  scratch_object, scratch_project, costume_resolution):
        # some initial Scratch settings are done with a general JSON configuration instead with blocks. Here the equivalent bricks are added for Catrobat.
        implicit_bricks_to_add = []

        # create AddItemToUserListBrick bricks to populate user lists with their default values
        # global lists will be populated in StartScript of background/stage sprite object
        if scratch_object.is_stage() and scratch_object.get_lists() is not None:
            for global_user_list_data in scratch_project.global_user_lists:
                list_name = global_user_list_data["listName"]
                assert len(list_name) > 0
                catr_user_list = catrobat.find_global_user_list_by_name(catrobat_project, sprite, list_name)
                if "contents" not in global_user_list_data:
                    continue
                for value in global_user_list_data["contents"]:
                    catr_value_formula = catrobat.create_formula_with_value(value)
                    implicit_bricks_to_add += [catbricks.AddItemToUserListBrick(catr_value_formula, catr_user_list)]

        if not scratch_object.is_stage() and scratch_object.get_lists() is not None:
            for user_list_data in scratch_object.get_lists():
                list_name = user_list_data["listName"]
                assert len(list_name) > 0
                catr_user_list = catrobat.find_sprite_user_list_by_name(catrobat_project, sprite, list_name)
                assert catr_user_list
                if "contents" not in user_list_data:
                    continue
                for value in user_list_data["contents"]:
                    catr_value_formula = catrobat.create_formula_with_value(value)
                    implicit_bricks_to_add += [catbricks.AddItemToUserListBrick(catr_value_formula, catr_user_list)]

        # object's currentCostumeIndex determines active costume at startup
        sprite_startup_look_idx = scratch_object.get_currentCostumeIndex()
        if sprite_startup_look_idx is not None:
            if isinstance(sprite_startup_look_idx, float):
                sprite_startup_look_idx = int(round(sprite_startup_look_idx))
            if sprite_startup_look_idx != 0:
                spriteStartupLook = sprite.getLookDataList()[sprite_startup_look_idx]
                set_look_brick = catbricks.SetLookBrick()
                set_look_brick.setLook(spriteStartupLook)
                implicit_bricks_to_add += [set_look_brick]

        # object's scratchX and scratchY Keys determine position
        x_pos = int(scratch_object.get_scratchX() or 0)
        y_pos = int(scratch_object.get_scratchY() or 0)
        if x_pos != 0 or y_pos != 0:
            implicit_bricks_to_add += [catbricks.PlaceAtBrick(x_pos, y_pos)]

        object_relative_scale = scratch_object.get_scale() or 1
        if costume_resolution is not None:
            object_scale = object_relative_scale * 100.0 / costume_resolution
            if object_scale != 100.0:
                implicit_bricks_to_add += [catbricks.SetSizeToBrick(object_scale)]

        object_rotation_in_degrees = float(scratch_object.get_direction() or 90.0)
        number_of_full_object_rotations = int(round(object_rotation_in_degrees/360.0))
        effective_object_rotation_in_degrees = object_rotation_in_degrees - 360.0 * number_of_full_object_rotations
        if effective_object_rotation_in_degrees != 90.0:
            implicit_bricks_to_add += [catbricks.PointInDirectionBrick(effective_object_rotation_in_degrees)]

        object_visible = scratch_object.get_visible()
        if object_visible is not None and not object_visible:
            implicit_bricks_to_add += [catbricks.HideBrick()]

        rotation_style = scratch_object.get_rotationStyle()
        if rotation_style is not None:
            traverser = _BlocksConversionTraverser(sprite, catrobat_project)
            if rotation_style == "leftRight":
                set_rotation_style_brick = traverser._converted_helper_brick_or_formula_element(["left-right"], "setRotationStyle")
                assert set_rotation_style_brick is not None
                implicit_bricks_to_add += [set_rotation_style_brick]
            elif rotation_style == "none":
                set_rotation_style_brick = traverser._converted_helper_brick_or_formula_element(["don't rotate"], "setRotationStyle")
                assert set_rotation_style_brick is not None
                implicit_bricks_to_add += [set_rotation_style_brick]

        if len(implicit_bricks_to_add) > 0:
            catrobat.add_to_start_script(implicit_bricks_to_add, sprite)

        # initialization of object's variables
        for scratch_variable in scratch_object.get_variables():
            if scratch_variable["name"] == _SHARED_GLOBAL_ANSWER_VARIABLE_NAME:
                continue

            args = [catrobat_scene, scratch_variable["name"], scratch_variable["value"], sprite]
            try:
                _assign_initialization_value_to_user_variable(*args)
            except:
                log.error("Cannot assign initialization value {} to user variable {}"
                          .format(scratch_variable["name"], scratch_variable["value"]))

        # if this sprite object contains a script that first added AskBrick or accessed the
        # (global) answer variable, the (global) answer variable gets initialized by adding a
        # SetVariable brick with an empty string-initialization value (i.e. "")
        if sprite_context.created_shared_global_answer_user_variable:
            try:
                _assign_initialization_value_to_user_variable(catrobat_scene,
                                                              _SHARED_GLOBAL_ANSWER_VARIABLE_NAME,
                                                              "", sprite)
            except:
                log.error("Cannot assign initialization value {} to shared global answer user variable {}"
                          .format(scratch_variable["name"], scratch_variable["value"]))

        # TODO: Add ShowVariable Bricks for variables that are visible
        #       (also for "answer", i.e. _SHARED_GLOBAL_ANSWER_VARIABLE_NAME!!)

    @classmethod
    def _catrobat_script_from(cls, scratch_script, sprite, catrobat_project, context=None):
        if not isinstance(scratch_script, scratch.Script):
            raise common.ScratchtobatError("Arg1 must be of type={}, but is={}".format(scratch.Script, type(scratch_script)))
        if sprite and not isinstance(sprite, catbase.Sprite):
            raise common.ScratchtobatError("Arg2 must be of type={}, but is={}".format(catbase.Sprite, type(sprite)))

        log.info("  script type: %s, args: %s", scratch_script.type, scratch_script.arguments)
        try:
            cat_instance = _ScratchToCatrobat.create_script(scratch_script.type, scratch_script.arguments,
                                                            catrobat_project, sprite, context)
        except:
            log.exception("Unable to convert script! -> Replacing with StartScript")
            cat_instance = catbase.StartScript()
            cat_instance.addBrick(_placeholder_for_unmapped_blocks_to("UNSUPPORTED SCRIPT", scratch_script.type))

        script_context = ScriptContext(context)
        converted_bricks = cls._catrobat_bricks_from(scratch_script.script_element, sprite, script_context)

        assert isinstance(converted_bricks, list) and len(converted_bricks) == 1
        [converted_bricks] = converted_bricks

        log.debug("   --> converted: <%s>", ", ".join(map(catrobat.simple_name_for, converted_bricks)))
        ignored_blocks = 0
        for brick in converted_bricks:
            # Scratch behavior: blocks can be ignored e.g. if no arguments are set
            if not brick:
                ignored_blocks += 1
                continue
            try:
                if not isinstance(cat_instance, catbricks.UserBrick):
                    assert isinstance(cat_instance, catbase.Script)
                    cat_instance.addBrick(brick)
                else:
                    cat_instance.appendBrickToScript(brick)
            except TypeError:
                if isinstance(brick, (str, unicode)):
                    log.error("string brick: %s", brick)
                else:
                    log.error("type: %s, value: %s", brick.type, brick.value)
                assert False
        if ignored_blocks > 0:
            log.info("number of ignored Scratch blocks: %d", ignored_blocks)
        return cat_instance

    @classmethod
    def _catrobat_bricks_from(cls, scratch_blocks, catrobat_sprite, script_context=None):
        if not isinstance(scratch_blocks, scratch.ScriptElement):
            scratch_blocks = scratch.ScriptElement.from_raw_block(scratch_blocks)
        traverser = _BlocksConversionTraverser(catrobat_sprite, cls._catrobat_project, script_context)
        traverser.traverse(scratch_blocks)
        return traverser.converted_bricks


class ConvertedProject(object):

    def __init__(self, catrobat_project, scratch_project):
        self.scratch_project = scratch_project
        self.catrobat_program = catrobat_project
        self.name = self.catrobat_program.getXmlHeader().getProgramName()

    @staticmethod
    def _converted_output_path(output_dir, project_name):
        return os.path.join(output_dir, catrobat.encoded_project_name(project_name) + catrobat.PACKAGED_PROGRAM_FILE_EXTENSION)

    def save_as_catrobat_package_to(self, output_dir, archive_name=None, progress_bar=None, context=None):

        def iter_dir(path):
            for root, _, files in os.walk(path):
                for file_ in files:
                    yield os.path.join(root, file_)
        log.info("convert Scratch project to '%s'", output_dir)

        with common.TemporaryDirectory() as catrobat_program_dir:
            self.save_as_catrobat_directory_structure_to(catrobat_program_dir, progress_bar, context)
            common.makedirs(output_dir)
            archive_name = self.name if archive_name is None else archive_name
            catrobat_zip_file_path = self._converted_output_path(output_dir, archive_name)
            log.info("  save packaged Scratch project to '%s'", catrobat_zip_file_path)
            if os.path.exists(catrobat_zip_file_path):
                os.remove(catrobat_zip_file_path)
            with zipfile.ZipFile(catrobat_zip_file_path, 'w') as zip_fp:
                for file_path in iter_dir(unicode(catrobat_program_dir)):
                    assert isinstance(file_path, unicode)
                    path_inside_zip = file_path.replace(catrobat_program_dir, u"")
                    zip_fp.write(file_path, path_inside_zip)
            assert os.path.exists(catrobat_zip_file_path), "Catrobat package not written: %s" % catrobat_zip_file_path
        return catrobat_zip_file_path

    @staticmethod
    def _images_dir_of_project(temp_dir):
        return os.path.join(temp_dir, CATROBAT_DEFAULT_SCENE_NAME, "images")

    @staticmethod
    def _sounds_dir_of_project(temp_dir):
        return os.path.join(temp_dir, CATROBAT_DEFAULT_SCENE_NAME, "sounds")

    def save_as_catrobat_directory_structure_to(self, temp_path, progress_bar=None, context=None):
        def create_directory_structure():
            sounds_path = self._sounds_dir_of_project(temp_path)
            os.makedirs(sounds_path)

            images_path = self._images_dir_of_project(temp_path)
            os.makedirs(images_path)

            for _ in (temp_path, sounds_path, images_path):
                # TODO: into common module
                open(os.path.join(_, catrobat.ANDROID_IGNORE_MEDIA_MARKER_FILE_NAME), 'a').close()
            return sounds_path, images_path

        def program_source_for(catrobat_program):
            storage_handler = catio.StorageHandler()
            code_xml_content = storage_handler.XML_HEADER
            code_xml_content += storage_handler.getXMLStringOfAProject(catrobat_program)
            return code_xml_content

        def write_program_source(catrobat_program, context):
            program_source = program_source_for(catrobat_program)
            with open(os.path.join(temp_path, catrobat.PROGRAM_SOURCE_FILE_NAME), "wb") as fp:
                fp.write(program_source.encode("utf8"))

            # copying key images needed for keyPressed substitution
            for listened_key in self.scratch_project.listened_keys:
                key_image_path = _key_image_path_for(listened_key)
                shutil.copyfile(key_image_path, os.path.join(images_path, _key_filename_for(listened_key)))

        def download_automatic_screenshot_if_available(output_dir, scratch_project):
            if scratch_project.automatic_screenshot_image_url is None:
                return

            _AUTOMATIC_SCREENSHOT_FILE_NAME = helpers.catrobat_info("automatic_screenshot_file_name")
            download_file_path = os.path.join(output_dir, _AUTOMATIC_SCREENSHOT_FILE_NAME)
            common.download_file(scratch_project.automatic_screenshot_image_url, download_file_path)

        # TODO: rename/rearrange abstracting methods
        log.info("  Creating Catrobat project structure")
        sounds_path, images_path = create_directory_structure()

        log.info("  Saving media files")
        media_converter = mediaconverter.MediaConverter(self.scratch_project, self.catrobat_program,
                                                        images_path, sounds_path)
        media_converter.convert(progress_bar)

        log.info("  Saving project XML file")
        write_program_source(self.catrobat_program, context)
        log.info("  Downloading and adding automatic screenshot")
        download_automatic_screenshot_if_available(os.path.join(temp_path, CATROBAT_DEFAULT_SCENE_NAME), self.scratch_project)
        if progress_bar != None:
            progress_bar.update(ProgressType.SAVE_XML, progress_bar.saving_xml_progress_weight)

# TODO: could be done with just user_variables instead of project object
def _add_new_user_variable_with_initialization_value(project, variable_name, variable_value, sprite, sprite_name=None):
    user_variable = catrobat.add_user_variable(project, variable_name, sprite=sprite, sprite_name=sprite_name)
    assert user_variable is not None
    variable_initialization_brick = _create_variable_brick(variable_value, user_variable, catbricks.SetVariableBrick)
    catrobat.add_to_start_script([variable_initialization_brick], sprite)

def _assign_initialization_value_to_user_variable(scene, variable_name, variable_value, sprite):
    user_variable = scene.getDataContainer().getUserVariable(variable_name, sprite)
    assert user_variable is not None and user_variable.getName() == variable_name, \
           "variable: %s, sprite_name: %s" % (variable_name, sprite.getName())
    variable_initialization_brick = _create_variable_brick(variable_value, user_variable, catbricks.SetVariableBrick)
    catrobat.add_to_start_script([variable_initialization_brick], sprite, position=0)

# based on: http://stackoverflow.com/a/4274204
def _register_handler(dict_, *names):
    def dec(f):
        m_name = f.__name__
        for name in names:
            dict_[name] = m_name
        return f
    return dec

class _BlocksConversionTraverser(scratch.AbstractBlocksTraverser):

    _block_name_to_handler_map = {}

    def __init__(self, catrobat_sprite, catrobat_project, script_context=None):
        assert catrobat_sprite is not None
        assert catrobat_project is not None
        self.script_context = script_context if script_context is not None else ScriptContext()
        self.script_element = None
        self.sprite = catrobat_sprite
        self.project = catrobat_project
        self.scene = catrobat_project.getDefaultScene()
        self.CatrobatClass = None
        self.arguments = None
        self._stack = []
        self._child_stack = []

    @property
    def stack(self):
        return self.converted_bricks

    @property
    def converted_bricks(self):
        return self._stack

    def traverse(self, script_element):
        self._stack += [script_element.name]
        super(_BlocksConversionTraverser, self).traverse(script_element)

    def _pop_stack(self, start_index):
        popped = list(self._stack[start_index:])
        del self._stack[start_index:]
        return popped

    def _visit(self, script_element):
        self.script_element = script_element
        arguments_start_index = len(self._stack) - self._stack[::-1].index(script_element.name)
        self.arguments = self._pop_stack(arguments_start_index)

        new_stack_values = self._converted_script_element()

        del self._stack[-1]
        if not isinstance(new_stack_values, list):
            new_stack_values = [new_stack_values]

        # TODO: simplify this...
        if len(self._child_stack) > 0 and len(new_stack_values) == len([val for val in new_stack_values if isinstance(val, catbricks.Brick)]):
            for brick_list in reversed(self._child_stack):
                self._stack += brick_list
            self._child_stack = []

        if len(new_stack_values) > 1 and isinstance(new_stack_values[-1], catformula.FormulaElement):
            # TODO: lambda check if all entries are instance of Brick
            self._child_stack += [new_stack_values[:-1]]
            new_stack_values = [new_stack_values[-1]]

        self._stack += new_stack_values

    def _converted_script_element(self):
        script_element = self.script_element
        if script_element.name == "computeFunction:of:":
            # removing block name which is common prefix for all function blocks:
            # [Block("computeFunction:of:"), BlockValue("tan"), ...] is changed to [Block("tan"), ...]
            assert len(self.arguments) >= 1
            self.script_element = scratch.Block(name=self.arguments[0])
            self.arguments = self.arguments[1:]

        self.block_name = block_name = self.script_element.name

        if isinstance(self.script_element, scratch.Block):
            log.debug("    block to convert: %s, arguments: %s",
                      block_name, catrobat.simple_name_for(self.arguments))

            unmapped_block_arguments = filter(lambda arg: isinstance(arg, UnmappedBlock), self.arguments)
            unsupported_blocks = map(lambda unmapped_block: unmapped_block.to_placeholder_brick(self.block_name)[0], unmapped_block_arguments)
            self.arguments = map(lambda arg: catrobat.create_formula_element_with_value(0) if isinstance(arg, UnmappedBlock) else arg, self.arguments)
            self.CatrobatClass = _ScratchToCatrobat.catrobat_brick_class_for(block_name)
            handler_method_name = self._block_name_to_handler_map.get(block_name)
            try:
                if handler_method_name is not None:
                    converted_element = getattr(self, handler_method_name)()
                else:
                    converted_element = self._regular_block_conversion()
                converted_element = converted_element if isinstance(converted_element, list) else [converted_element]
                converted_element = unsupported_blocks + converted_element
            except Exception as e:
                log.warn("  " + ">" * 78)
                log.warn("  Replacing {0} with NoteBrick".format(block_name))
                log.warn("  Exception: {0}, ".format(e.message), exc_info=1)
                converted_element = _placeholder_for_unmapped_blocks_to(block_name)
        elif isinstance(self.script_element, scratch.BlockValue):
            converted_element = [script_element.name]
        else:
            assert isinstance(self.script_element, scratch.BlockList)
            # TODO: readability
            converted_element = [[arg2 for arg1 in self.arguments \
                                            for arg2 in (arg1.to_placeholder_brick(self.block_name) \
                                                if isinstance(arg1, UnmappedBlock) else [arg1])]]
        return converted_element

    def _regular_block_conversion(self):
        CatrobatClass = self.CatrobatClass
        # TODO: replace with UnmappedBlock as a None object
        if CatrobatClass is not None:
            is_catrobat_enum = not hasattr(CatrobatClass, "__module__") and hasattr(CatrobatClass, "getClass")
            self.arguments = _with_unmapped_blocks_replaced_as_default_formula_value(self.arguments)
            for try_number in range(6):
                try:
                    # TODO: simplify
                    if try_number == 0:
                        converted_args = [common.int_or_float(arg) or arg if isinstance(arg, (str, unicode)) else arg for arg in self.arguments]
                    elif try_number == 1:
                        converted_args = [catformula.FormulaElement(catElementType.NUMBER, str(arg), None) if isinstance(arg, numbers.Number) else arg for arg in converted_args]  # @UndefinedVariable
                    elif try_number == 4:
                        converted_args = self.arguments
                    elif try_number == 2:
                        args = [arg if arg != None else "" for arg in self.arguments]
                        converted_args = [catrobat.create_formula_with_value(arg) for arg in args]
                    elif try_number == 3:
                        if len(self.arguments) == 2 and self.arguments[0] in { "brightness", "color", "ghost" }:
                            converted_args = [self.arguments[0]] + [catrobat.create_formula_with_value(arg) for arg in self.arguments[1:]]

                    if not is_catrobat_enum:
                        converted_value = CatrobatClass(*converted_args)
                    else:
                        converted_value = catrobat.formula_element_for(CatrobatClass, converted_args)
                    assert converted_value, "No result for {} with args {}".format(self.block_name, converted_args)
                    break
                except (TypeError) as e:
                    log.debug("instantiation try %d failed for class: %s, raw_args: %s, Catroid args: %s",
                              try_number, CatrobatClass, self.arguments, map(catrobat.simple_name_for, converted_args))
                    class_exception = e
            else:
                log.error("General instantiation failed for class: %s, raw_args: %s, Catroid args: %s",
                          CatrobatClass, self.arguments, map(catrobat.simple_name_for, converted_args))
                raise class_exception
                log.exception(class_exception)
                self.errors += [class_exception]
            new_stack_values = converted_value
        else:
            log.debug("no Class for: %s, args: %s", self.block_name, map(catrobat.simple_name_for, self.arguments))
            new_stack_values = UnmappedBlock(self.sprite, *([self.block_name] + self.arguments))
        return new_stack_values

    def _converted_helper_brick_or_formula_element(self, arguments, block_name):
        preserved_args = self.arguments
        self.arguments = arguments
        preserved_catrobat_class = self.CatrobatClass
        self.CatrobatClass = _ScratchToCatrobat.complete_mapping.get(block_name)
        handler_method_name = self._block_name_to_handler_map.get(block_name)
        if handler_method_name:
            converted_element = getattr(self, handler_method_name)()
        else:
            converted_element = self._regular_block_conversion()
        self.arguments = preserved_args
        self.CatrobatClass = preserved_catrobat_class
        return converted_element

    # formula element blocks (compute, operator, ...)
    @_register_handler(_block_name_to_handler_map, "()")
    def _convert_bracket_block(self):
        # NOTE: this operator is only used internally and not part of Scratch
        [value] = self.arguments
        formula_element = catformula.FormulaElement(catElementType.BRACKET, None, None)
        formula_element.setRightChild(value)
        return formula_element

    @_register_handler(_block_name_to_handler_map, "10 ^")
    def _convert_pow_of_10_block(self):
        [value] = self.arguments

        # unfortunately 10^x and pow(x) functions are not yet available in Catroid
        # but Catroid already supports exp(x) and ln(x) functions
        # since 10^x == exp(x*ln(10)) we can use 3 math functions to achieve the correct result!

        # ln(10)
        ln_formula_elem = self._converted_helper_brick_or_formula_element([10], "ln")

        # x*ln(10)     (where x:=value)
        exponent_formula_elem = self._converted_helper_brick_or_formula_element([value, ln_formula_elem], "*")

        # exp(x*ln(10))
        result_formula_elem = self._converted_helper_brick_or_formula_element([exponent_formula_elem], "e^")

        # round(exp(x*ln(10)))     (use round-function to get rid of rounding errors)
        return self._converted_helper_brick_or_formula_element([result_formula_elem], "rounded")

    @_register_handler(_block_name_to_handler_map, "lineCountOfList:")
    def _convert_line_count_of_list_block(self):
        [list_name] = self.arguments
        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.scene, self.sprite, list_name)
        assert user_list is not None
        left_formula_elem = catformula.FormulaElement(catElementType.USER_LIST, list_name, None)
        formula_element = catformula.FormulaElement(catElementType.FUNCTION, self.CatrobatClass.toString(), None)
        formula_element.setLeftChild(left_formula_elem)
        return formula_element

    @_register_handler(_block_name_to_handler_map, "list:contains:")
    def _convert_list_contains_block(self):
        [list_name, value] = self.arguments
        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.scene, self.sprite, list_name)
        assert user_list is not None
        left_formula_elem = catformula.FormulaElement(catElementType.USER_LIST, list_name, None)
        formula_element = catformula.FormulaElement(catElementType.FUNCTION, self.CatrobatClass.toString(), None)
        formula_element.setLeftChild(left_formula_elem)
        formula_element.setRightChild(catrobat.create_formula_element_with_value(value))
        return formula_element

    @_register_handler(_block_name_to_handler_map, "getLine:ofList:")
    def _convert_get_line_of_list_block(self):
        [position, list_name] = self.arguments
        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.scene, self.sprite, list_name)
        assert user_list is not None

        if position == "last":
            index_formula_element = self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:")
        elif position == "random":
            start_formula_element = catformula.FormulaElement(catElementType.NUMBER, "1", None) # first index of list
            end_formula_element = self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:")
            index_formula_element = self._converted_helper_brick_or_formula_element([start_formula_element, end_formula_element], "randomFrom:to:")
        else:
            index_formula_element = catrobat.create_formula_element_with_value(position)

        right_formula_elem = catformula.FormulaElement(catElementType.USER_LIST, list_name, None)
        formula_element = catformula.FormulaElement(catElementType.FUNCTION, self.CatrobatClass.toString(), None)
        formula_element.setLeftChild(index_formula_element)
        formula_element.setRightChild(right_formula_elem)
        return formula_element

    @_register_handler(_block_name_to_handler_map, "stringLength:")
    def _convert_string_length_block(self):
        [value] = self.arguments
        left_formula_elem = catrobat.create_formula_element_with_value(value)
        formula_element = catformula.FormulaElement(catElementType.FUNCTION, self.CatrobatClass.toString(), None)
        formula_element.setLeftChild(left_formula_elem)
        return formula_element

    @_register_handler(_block_name_to_handler_map, "letter:of:")
    def _convert_letter_of_block(self):
        [index, value] = self.arguments
        index_formula_elem = catrobat.create_formula_element_with_value(index)
        value_formula_elem = catrobat.create_formula_element_with_value(value)
        formula_element = catformula.FormulaElement(catElementType.FUNCTION, self.CatrobatClass.toString(), None)
        formula_element.setLeftChild(index_formula_elem)
        formula_element.setRightChild(value_formula_elem)
        return formula_element

    @_register_handler(_block_name_to_handler_map, "concatenate:with:")
    def _convert_concatenate_with_block(self):
        [value1, value2] = self.arguments
        formula_element = catformula.FormulaElement(catElementType.FUNCTION, self.CatrobatClass.toString(), None)
        value1_formula_elem = catrobat.create_formula_element_with_value(value1)
        formula_element.setLeftChild(value1_formula_elem)
        value2_formula_elem = catrobat.create_formula_element_with_value(value2)
        formula_element.setRightChild(value2_formula_elem)
        return formula_element

    # action and other blocks
    @_register_handler(_block_name_to_handler_map, "doRepeat", "doForever")
    def _convert_loop_blocks(self):
        brick_arguments = self.arguments
        if self.block_name == 'doRepeat':
            times_value, nested_bricks = brick_arguments
            catr_loop_start_brick = self.CatrobatClass(catrobat.create_formula_with_value(times_value))
        else:
            assert self.block_name == 'doForever', self.block_name
            [nested_bricks] = brick_arguments
            catr_loop_start_brick = self.CatrobatClass()
        return [catr_loop_start_brick] + nested_bricks + [catbricks.LoopEndBrick(catr_loop_start_brick)]

    @_register_handler(_block_name_to_handler_map, "doUntil")
    def _convert_do_until_block(self):
        condition, nested_bricks = self.arguments
        repeat_until_brick = self.CatrobatClass(catrobat.create_formula_with_value(condition))
        return [repeat_until_brick] + nested_bricks + [catbricks.LoopEndBrick(repeat_until_brick)]

    @_register_handler(_block_name_to_handler_map, "startScene")
    def _convert_scene_block(self):
        [look_name] = self.arguments

        #TODO: If SetBackgroundBrick gets Formula as accepted argument for Constructor,
        #      then extend this register_handler accordingly.

        if look_name == "next backdrop":
            return catbricks.NextLookBrick()
        if look_name == "previous backdrop":
            return catbricks.PreviousLookBrick()

        background_sprite = catrobat.background_sprite_of(self.scene)
        if not background_sprite:
            assert catrobat.is_background_sprite(self.sprite)
            background_sprite = self.sprite
        matching_looks = [_ for _ in background_sprite.getLookDataList() if _.getLookName() == look_name]
        if not matching_looks:
            raise ConversionError("Background does not contain look with name: {}".format(look_name))
        assert len(matching_looks) == 1

        switch_background_brick = self.CatrobatClass()
        switch_background_brick.setLook(matching_looks[0])

        return switch_background_brick

    @_register_handler(_block_name_to_handler_map, "startSceneAndWait")
    def _convert_scene_and_wait_block(self):
        [look_name] = self.arguments

        #TODO: If SetBackgroundBrick gets Formula as accepted argument for Constructor,
        #      then extend this register_handler accordingly.

        if look_name == "next backdrop":
            return catbricks.NextLookBrick()
        if look_name == "previous backdrop":
            return catbricks.PreviousLookBrick()

        background_sprite = catrobat.background_sprite_of(self.scene)
        if not background_sprite:
            assert catrobat.is_background_sprite(self.sprite)
            background_sprite = self.sprite
        matching_looks = [_ for _ in background_sprite.getLookDataList() if _.getLookName() == look_name]
        if not matching_looks:
            raise ConversionError("Background does not contain look with name: {}".format(look_name))
        assert len(matching_looks) == 1

        switch_background_brick = self.CatrobatClass()
        switch_background_brick.setLook(matching_looks[0])

        return switch_background_brick

    @_register_handler(_block_name_to_handler_map, "doIf")
    def _convert_if_block(self):
        assert len(self.arguments) == 2
        if_begin_brick = catbricks.IfThenLogicBeginBrick(catrobat.create_formula_with_value(self.arguments[0]))
        if_end_brick = catbricks.IfThenLogicEndBrick(if_begin_brick)
        if_bricks = self.arguments[1] or []
        assert isinstance(if_bricks, list)
        return [if_begin_brick] + if_bricks + [if_end_brick]

    @_register_handler(_block_name_to_handler_map, "doIfElse")
    def _convert_if_else_block(self):
        assert len(self.arguments) == 3
        if_begin_brick = catbricks.IfLogicBeginBrick(catrobat.create_formula_with_value(self.arguments[0]))
        if_else_brick = catbricks.IfLogicElseBrick(if_begin_brick)
        if_end_brick = catbricks.IfLogicEndBrick(if_else_brick, if_begin_brick)
        if_bricks, [else_bricks] = self.arguments[1], self.arguments[2:] or [[]]
        if_bricks = if_bricks if if_bricks != None else []
        else_bricks = else_bricks if else_bricks != None else []
        return [if_begin_brick] + if_bricks + [if_else_brick] + else_bricks + [if_end_brick]

    @_register_handler(_block_name_to_handler_map, "lookLike:")
    def _convert_look_block(self):
        set_look_brick = self.CatrobatClass()
        [look_name] = self.arguments
        assert isinstance(look_name, (str, unicode)), type(look_name)
        look = next((look for look in self.sprite.getLookDataList() if look.getLookName() == look_name), None)
        if look is None:
            log.error("Look name: '%s' not found in sprite '%s'. Available looks: %s", look_name, self.sprite.getName(), ", ".join([look.getLookName() for look in self.sprite.getLookDataList()]))
            return []
        else:
            set_look_brick.setLook(look)
            return [set_look_brick]

    @_register_handler(_block_name_to_handler_map, "showVariable:")
    def _convert_show_variable_block(self):
        [variable_name] = self.arguments
        user_variable = self.scene.getDataContainer().getUserVariable(variable_name, self.sprite)
        assert user_variable is not None # the variable must exist at this stage!
        assert user_variable.getName() == variable_name
        show_variable_brick = self.CatrobatClass(0, 0)
        show_variable_brick.setUserVariableName(variable_name)
        show_variable_brick.setUserVariable(user_variable)
        return show_variable_brick

    @_register_handler(_block_name_to_handler_map, "hideVariable:")
    def _convert_hide_variable_block(self):
        [variable_name] = self.arguments
        user_variable = self.scene.getDataContainer().getUserVariable(variable_name, self.sprite)
        assert user_variable is not None # the variable must exist at this stage!
        assert user_variable.getName() == variable_name
        hide_variable_brick = self.CatrobatClass()
        hide_variable_brick.setUserVariableName(variable_name)
        hide_variable_brick.setUserVariable(user_variable)
        return hide_variable_brick

    @_register_handler(_block_name_to_handler_map, "append:toList:")
    def _convert_append_to_list_block(self):
        [value, list_name] = self.arguments
        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.scene, self.sprite, list_name)
        assert user_list is not None
        value_formula = catrobat.create_formula_with_value(value)
        return self.CatrobatClass(value_formula, user_list)

    @_register_handler(_block_name_to_handler_map, "insert:at:ofList:")
    def _convert_insert_at_of_list_block(self):
        [value, position, list_name] = self.arguments
        if position == "last":
            return self._converted_helper_brick_or_formula_element([value, list_name], "append:toList:")
        elif position == "random":
            start_formula_element = catformula.FormulaElement(catElementType.NUMBER, "1", None) # first index of list
            end_formula_element = self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:")
            formula_element = self._converted_helper_brick_or_formula_element([start_formula_element, end_formula_element], "randomFrom:to:")
            index_formula = catrobat.create_formula_with_value(formula_element)
        else:
            index_formula = catrobat.create_formula_with_value(position)

        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.scene, self.sprite, list_name)
        assert user_list is not None
        value_formula = catrobat.create_formula_with_value(value)
        assert index_formula is not None
        return self.CatrobatClass(value_formula, index_formula, user_list)

    @_register_handler(_block_name_to_handler_map, "deleteLine:ofList:")
    def _convert_delete_line_of_list_block(self):
        [position, list_name] = self.arguments
        index_formula = None
        prepend_bricks = []
        append_bricks = []
        if position in ["last", "all"]:
            index_formula = catrobat.create_formula_with_value(self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:"))

            if position == "all":
                # repeat loop workaround...
                catr_loop_start_brick = catbricks.RepeatBrick(index_formula)
                prepend_bricks += [catr_loop_start_brick]
                append_bricks += [catbricks.LoopEndBrick(catr_loop_start_brick)]
                index_formula = catrobat.create_formula_with_value("1") # first item to be deleted for n-times!
        else:
            index_formula = catrobat.create_formula_with_value(position)

        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.scene, self.sprite, list_name)
        assert user_list is not None
        assert index_formula is not None
        return prepend_bricks + [self.CatrobatClass(index_formula, user_list)] + append_bricks

    @_register_handler(_block_name_to_handler_map, "setLine:ofList:to:")
    def _convert_set_line_of_list_to_block(self):
        [position, list_name, value] = self.arguments
        if position == "last":
            index_formula = catrobat.create_formula_with_value(self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:"))
        elif position == "random":
            start_formula_element = catformula.FormulaElement(catElementType.NUMBER, "1", None) # first index of list
            end_formula_element = self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:")
            index_formula_element = self._converted_helper_brick_or_formula_element([start_formula_element, end_formula_element], "randomFrom:to:")
            index_formula = catrobat.create_formula_with_value(index_formula_element)
        else:
            index_formula = catrobat.create_formula_with_value(position)

        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.scene, self.sprite, list_name)
        assert user_list is not None
        value_formula = catrobat.create_formula_with_value(value)
        assert index_formula is not None
        return self.CatrobatClass(value_formula, index_formula, user_list)

    @_register_handler(_block_name_to_handler_map, "showList:")
    def _convert_show_list_block(self):
        #["showList:", "myList"] # for testing purposes...
        #[list_name] = self.arguments
        assert "IMPLEMENT THIS AS SOON AS CATROBAT SUPPORTS THIS!!"

    @_register_handler(_block_name_to_handler_map, "hideList:")
    def _convert_hide_list_block(self):
        #["hideList:", "myList"] # for testing purposes...
        #[list_name] = self.arguments
        assert "IMPLEMENT THIS AS SOON AS CATROBAT SUPPORTS THIS!!"

    @_register_handler(_block_name_to_handler_map, "playSound:")
    def _convert_sound_block(self):
        [sound_name], sound_list = self.arguments, self.sprite.getSoundList()
        sound_data = {sound_info.getTitle(): sound_info for sound_info in sound_list}.get(sound_name)
        if not sound_data:
            raise ConversionError("Sprite does not contain sound with name={}".format(sound_name))
        play_sound_brick = self.CatrobatClass()
        play_sound_brick.setSoundInfo(sound_data)
        return play_sound_brick

    @_register_handler(_block_name_to_handler_map, "doPlaySoundAndWait")
    def _convert_sound_and_wait_block(self):
        [sound_name], sound_list = self.arguments, self.sprite.getSoundList()
        sound_data = {sound_info.getTitle(): sound_info for sound_info in sound_list}.get(sound_name)
        if not sound_data:
            raise ConversionError("Sprite does not contain sound with name={}".format(sound_name))
        play_sound_and_wait_brick = self.CatrobatClass()
        play_sound_and_wait_brick.setSoundInfo(sound_data)
        return play_sound_and_wait_brick

    @_register_handler(_block_name_to_handler_map, "setGraphicEffect:to:")
    def _convert_set_graphic_effect_block(self):
        [effect_type, value] = self.arguments
        if effect_type == 'brightness':
            # range  Scratch:  -100 to 100  (default:   0)
            # range Catrobat:     0 to 200% (default: 100%)
            formula_elem = self._converted_helper_brick_or_formula_element([value, 100], "+")
            return catbricks.SetBrightnessBrick(catrobat.create_formula_with_value(formula_elem))
        elif effect_type == 'ghost':
            # range  Scratch:     0 to 100  (default:   0)
            # range Catrobat:     0 to 100% (default:   0%)
            return catbricks.SetTransparencyBrick(catrobat.create_formula_with_value(value))
        elif effect_type == 'color':
            # range  Scratch:     0 to 200  (default:   0)
            # range Catrobat:     0 to 200% (default:   0%)
            return catbricks.SetColorBrick(catrobat.create_formula_with_value(value))
        else:
            return _placeholder_for_unmapped_blocks_to("setGraphicEffect:to:", effect_type, value)

    @_register_handler(_block_name_to_handler_map, "changeGraphicEffect:by:")
    def _convert_change_graphic_effect_block(self):
        [effect_type, value] = self.arguments
        if effect_type == 'brightness':
            # range  Scratch:  -100 to 100  (default:   0)
            # range Catrobat:     0 to 200% (default: 100%)
            # since ChangeBrightnessByNBrick adds increment -> no range-conversion needed
            return catbricks.ChangeBrightnessByNBrick(catrobat.create_formula_with_value(value))
        elif effect_type == 'ghost':
            # range  Scratch:     0 to 100  (default:   0)
            # range Catrobat:     0 to 100% (default:   0%)
            return catbricks.ChangeTransparencyByNBrick(catrobat.create_formula_with_value(value))
        elif effect_type == 'color':
            # range  Scratch:     0 to 200  (default:   0)
            # range Catrobat:     0 to 200% (default:   0%)
            return catbricks.ChangeColorByNBrick(catrobat.create_formula_with_value(value))
        else:
            return _placeholder_for_unmapped_blocks_to("changeGraphicEffect:by:", effect_type, value)

    @_register_handler(_block_name_to_handler_map, "changeVar:by:", "setVar:to:")
    def _convert_variable_block(self):
        [variable_name, value] = self.arguments
        user_variable = self.scene.getDataContainer().getUserVariable(variable_name, self.sprite)
        if user_variable is None:
            # WORKAROUND: for generated variables added in preprocessing step
            # must be generated user variable, otherwise the variable must have already been added at this stage!
            assert(_is_generated(variable_name))
            catrobat.add_user_variable(self.project, variable_name, self.sprite, self.sprite.getName())
            user_variable = self.scene.getDataContainer().getUserVariable(variable_name, self.sprite)

        assert user_variable is not None and user_variable.getName() == variable_name, \
               "variable: %s, sprite_name: %s" % (variable_name, self.sprite.getName())
        return [self.CatrobatClass(value, user_variable)]

    @_register_handler(_block_name_to_handler_map, "say:duration:elapsed:from:")
    def _convert_say_duration_elapsed_from_block(self):
        [msg, duration] = self.arguments
        say_for_bubble_brick = self.CatrobatClass()
        say_for_bubble_brick.initializeBrickFields(catformula.Formula(msg),catformula.Formula(duration))
        return say_for_bubble_brick

    @_register_handler(_block_name_to_handler_map, "say:")
    def _convert_say_block(self):
        [msg] = self.arguments
        say_bubble_brick = self.CatrobatClass()
        say_bubble_brick.initializeBrickFields(catformula.Formula(msg))
        return say_bubble_brick

    @_register_handler(_block_name_to_handler_map, "think:duration:elapsed:from:")
    def _convert_think_duration_elapsed_from_block(self):
        [msg, duration] = self.arguments
        msg_formula = catrobat.create_formula_with_value(msg)
        duration_formula = catrobat.create_formula_with_value(duration)
        return self.CatrobatClass(msg_formula, duration_formula)

    @_register_handler(_block_name_to_handler_map, "think:")
    def _convert_think_block(self):
        [msg] = self.arguments
        think_bubble_brick = self.CatrobatClass()
        think_bubble_brick.initializeBrickFields(catrobat.create_formula_with_value(msg))
        return think_bubble_brick

    @_register_handler(_block_name_to_handler_map, "doAsk")
    def _convert_do_ask_block(self):
        [question] = self.arguments
        data_container = self.scene.getDataContainer()
        question_formula = catrobat.create_formula_with_value(question)
        shared_global_answer_user_variable = _get_or_create_shared_global_answer_variable(self.project,
                                                                                          data_container,
                                                                                          self.script_context)
        return self.CatrobatClass(question_formula, shared_global_answer_user_variable)

    @_register_handler(_block_name_to_handler_map, "answer")
    def _convert_answer_block(self):
        data_container = self.scene.getDataContainer()
        shared_global_answer_user_variable = _get_or_create_shared_global_answer_variable(self.project,
                                                                                          data_container,
                                                                                          self.script_context)
        return _variable_for(shared_global_answer_user_variable.getName())

    @_register_handler(_block_name_to_handler_map, "createCloneOf")
    def _convert_create_clone_of_block(self):
        [base_sprite] = self.arguments
        if isinstance(base_sprite, catformula.FormulaElement):
            return catbricks.NoteBrick("Can't convert Clone-Brick with Formula as argument.")

        if len(base_sprite) == 0:
            return catbricks.NoteBrick("Can't convert Clone-Brick with no argument.")

        if base_sprite == "_myself_" or base_sprite == self.sprite.getName():
            return self.CatrobatClass(self.sprite)

        if isinstance(base_sprite, basestring):
            for sprite in self.scene.spriteList:
                if sprite.getName() == base_sprite:
                    return self.CatrobatClass(sprite)
            if base_sprite in self.script_context.sprite_context.context.upcoming_sprites:
                new_sprite = self.script_context.sprite_context.context.upcoming_sprites[base_sprite]
            else:
                new_sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, base_sprite)
                self.script_context.sprite_context.context.upcoming_sprites[new_sprite.getName()] = new_sprite

            create_clone_of_brick = self.CatrobatClass(new_sprite)
            return create_clone_of_brick

    @_register_handler(_block_name_to_handler_map, "timeAndDate")
    def _convert_time_and_date_block(self):
        [time_or_date] = self.arguments
        switcher = {
            "second": str(catformula.Sensors.TIME_SECOND),
            "minute": str(catformula.Sensors.TIME_MINUTE),
            "hour": str(catformula.Sensors.TIME_HOUR),
            "day of week": str(catformula.Sensors.DATE_WEEKDAY),
            "date": str(catformula.Sensors.DATE_DAY),
            "month": str(catformula.Sensors.DATE_MONTH),
            "year": str(catformula.Sensors.DATE_YEAR)
        }
        converted_time_or_date = switcher.get(time_or_date, "ERROR")
        if converted_time_or_date == "ERROR":
            return catbricks.NoteBrick("Can't convert Time-And-Date Block.")
        time_formula = catformula.FormulaElement(catformula.FormulaElement.ElementType.SENSOR,
                                                 converted_time_or_date, None)
        if time_or_date == "day of week":
            time_formula = self._converted_helper_brick_or_formula_element([time_formula, 1], "+")
        return time_formula

    @_register_handler(_block_name_to_handler_map, "penColor:")
    def _convert_pen_color_block(self):
        [int_color_value] = self.arguments
        if isinstance(int_color_value, int):
            color = Color(int_color_value)
            red, green, blue = color.getRed(), color.getGreen(), color.getBlue()
            #creating uservariables
            red_uv, green_uv, blue_uv = catformula.UserVariable("red"), catformula.UserVariable("green"), \
                                        catformula.UserVariable("blue")
            red_uv.value, green_uv.value, blue_uv.value = catformula.Formula(red), \
                                                          catformula.Formula(green), \
                                                          catformula.Formula(blue)
            catrobat.add_user_variable(self.project, "red", self.sprite, self.sprite.getName())
            catrobat.add_user_variable(self.project, "green", self.sprite, self.sprite.getName())
            catrobat.add_user_variable(self.project, "blue", self.sprite, self.sprite.getName())
            red_sv = catbricks.SetVariableBrick(catformula.Formula(red), red_uv)
            green_sv = catbricks.SetVariableBrick(catformula.Formula(green), green_uv)
            blue_sv = catbricks.SetVariableBrick(catformula.Formula(blue), blue_uv)

            return [red_sv, green_sv, blue_sv, self.CatrobatClass(red, green, blue)]
        elif isinstance(int_color_value, catformula.FormulaElement):
            blue = self._converted_helper_brick_or_formula_element([int_color_value, 256], "%")

            blue_parenth = self._converted_helper_brick_or_formula_element([blue], "()")
            x_minus_blue = self._converted_helper_brick_or_formula_element([int_color_value, blue_parenth], "-")
            xmb_parenth = self._converted_helper_brick_or_formula_element([x_minus_blue], "()")
            xmb_divided_256 = self._converted_helper_brick_or_formula_element([xmb_parenth, 256], "/")
            xmbd_256_parenth = self._converted_helper_brick_or_formula_element([xmb_divided_256], "()")
            green = self._converted_helper_brick_or_formula_element([xmbd_256_parenth, 256], "%")

            green_parenth = self._converted_helper_brick_or_formula_element([green], "()")
            xmbd_256_minus_green = self._converted_helper_brick_or_formula_element([xmbd_256_parenth, green_parenth], "-")
            xmbd_256_mg_parenth = self._converted_helper_brick_or_formula_element([xmbd_256_minus_green], "()")
            red = self._converted_helper_brick_or_formula_element([xmbd_256_mg_parenth, 256], "/")

            #_create_variable_brick(value, user_variable, Class)
            red_uv, green_uv, blue_uv = catformula.UserVariable("red"), catformula.UserVariable("green"), \
                                        catformula.UserVariable("blue")
            red_uv.value, green_uv.value, blue_uv.value = catformula.Formula(red), catformula.Formula(green),\
                                                          catformula.Formula(blue)
            catrobat.add_user_variable(self.project, "red", self.sprite, self.sprite.getName())
            catrobat.add_user_variable(self.project, "green", self.sprite, self.sprite.getName())
            catrobat.add_user_variable(self.project, "blue", self.sprite, self.sprite.getName())
            red_sv = catbricks.SetVariableBrick(catformula.Formula(red), red_uv)
            green_sv = catbricks.SetVariableBrick(catformula.Formula(green), green_uv)
            blue_sv = catbricks.SetVariableBrick(catformula.Formula(blue), blue_uv)

            return [red_sv, green_sv, blue_sv, self.CatrobatClass(catformula.Formula(red), catformula.Formula(green), catformula.Formula(blue))]
        else:
            return catbricks.NoteBrick("Unsupported Argument Type")

    @_register_handler(_block_name_to_handler_map, "penSize:")
    def _convert_pen_size_block(self):
        [pen_size] = self.arguments
        pen_size_uv = catformula.UserVariable("pen_size")
        pen_size_uv.value = catformula.Formula(pen_size)
        catrobat.add_user_variable(self.project, "pen_size", self.sprite, self.sprite.getName())
        pen_size_sv = catbricks.SetVariableBrick(catformula.Formula(pen_size), pen_size_uv)
        return [pen_size_sv, self.CatrobatClass(catformula.Formula(pen_size))]

#     @_register_handler(_block_name_to_handler_map, "changePenHueBy:")
#     def _convert_change_pen_color_block(self):
#         [hue] = self.arguments
#         #TODO: get old color on old_color
#         r_, g_, b_ = old_color.getRed()/255.0, old_color.getGreen()/255.0, old_color.getBlue()/255.0
#         Cmax, Cmin = max([r_, g_, b_]), min([r_, g_, b_])
#         delta = Cmax - Cmin
#
#         h, s, v = 0, 0, Cmax
#
#         if delta == 0:
#             h = 0
#         elif Cmax == r_:
#             h = 60*(((g_-b_)/delta)%6)
#         elif Cmax == g_:
#             h = 60*(((b_-r_)/delta)+2)
#         elif Cmax == b_:
#             h = 60*(((r_-g_)/delta)+4)
#
#         if Cmax == 0:
#             s = 0
#         else:
#             s = delta/Cmax
#
#         if h + hue > 360:
#             h = (h + hue) % 360
#         else:
#             h = h + hue
#
#         C = v*s
#         X = C*(1-abs( ( (h/60) % 2) -1 ) )
#         m = v - C
#
#         if h < 60 and h >= 0:
#             r_, g_, b_ = C, X, 0
#         if h < 120 and h >= 60:
#             r_, g_, b_ = X, C, 0
#         if h < 180 and h >= 120:
#             r_, g_, b_ = 0, C, X
#         if h < 240 and h >= 180:
#             r_, g_, b_ = 0, X, C
#         if h < 300 and h >= 240:
#             r_, g_, b_ = X, 0, C
#         if h < 360 and h >= 300:
#             r_, g_, b_ = C, 0, X
#
#         r, g, b = (r_ + m) * 255, (g_ + m) * 255, (b_ + m) * 255
#         new_color = Color(int(r), int(g), int(b))
#         return catbricks.SetPenColorBrick(new_color.getRed(), new_color.getGreen(), new_color.getBlue())
#
#     @_register_handler(_block_name_to_handler_map, "changePenSizeBy:")
#     def _convert_change_pen_size_block(self):
#         [size_add] = self.arguments
#         #TODO: get old pen size
#         return catbricks.SetPenSizeBrick(int(old_pen_size) + size_add)

    @_register_handler(_block_name_to_handler_map, "setRotationStyle")
    def _convert_set_rotation_style_block(self):
        [style] = self.arguments
        set_rotation_style_brick = self.CatrobatClass()
        set_rotation_style_brick.selection = ["left-right", "all around", "don't rotate"].index(style)
        return set_rotation_style_brick

    @_register_handler(_block_name_to_handler_map, "call")
    def _convert_call_block(self):
        arguments = self.arguments
        scratch_function_header = arguments[0]
        param_values = arguments[1:]
        sprite_context = self.script_context.sprite_context
        return _create_user_brick(sprite_context, scratch_function_header, param_values, declare=False)

    @_register_handler(_block_name_to_handler_map, "gotoSpriteOrMouse:")
    def _convert_go_to_sprite_or_mouse_block(self):
        [base_sprite], go_to_brick = self.arguments, None
        if base_sprite == "_mouse_":
            go_to_brick = self.CatrobatClass()
            go_to_brick.spinnerSelection = 0 # TODO: these value will change after updating Catroid class hierarchy (see: BrickValues class)
        elif base_sprite == "_random_":
            go_to_brick = self.CatrobatClass()
            go_to_brick.spinnerSelection = 1 # TODO: these value will change after updating Catroid class hierarchy (see: BrickValues class)
        elif isinstance(base_sprite, basestring):
            for sprite in self.scene.spriteList:
                if sprite.getName() == base_sprite:
                    return self.CatrobatClass(sprite)
            if base_sprite in self.script_context.sprite_context.context.upcoming_sprites:
                new_sprite = self.script_context.sprite_context.context.upcoming_sprites[base_sprite]
            else:
                new_sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, base_sprite)
                self.script_context.sprite_context.context.upcoming_sprites[new_sprite.getName()] = new_sprite

            go_to_brick = self.CatrobatClass(new_sprite)
        else:
            return catbricks.NoteBrick("Error: Not a valid parameter")
        return go_to_brick

    @_register_handler(_block_name_to_handler_map, "touching:")
    def _convert_touching(self):
        arguments = self.arguments
        if arguments[0] == "_mouse_":
            formula_element = catformula.FormulaElement(catElementType.SENSOR, None, None)
            formula_element.value = str(catformula.Sensors.COLLIDES_WITH_FINGER)
        elif arguments[0] == "_edge_":
            formula_element = catformula.FormulaElement(catElementType.SENSOR, None, None)
            formula_element.value = str(catformula.Sensors.COLLIDES_WITH_EDGE)
        else:
            formula_element = catformula.FormulaElement(catElementType.COLLISION_FORMULA, None, None)
            formula_element.value = arguments[0]
        return formula_element