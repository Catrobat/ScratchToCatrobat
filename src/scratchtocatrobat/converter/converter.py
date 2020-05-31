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
from __future__ import unicode_literals

import itertools
import numbers
import os
import shutil
import types
import zipfile
import re
import colorsys
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

BACKGROUND_LOCALIZED_GERMAN_NAME = "Hintergrund"
BACKGROUND_ORIGINAL_NAME = "Stage"

MOUSE_SPRITE_NAME = "_mouse_"
MOUSE_SPRITE_FILENAME = "mouse_cursor_dummy.png"

class KeyNames(object):
    ANY = "any"
    SPACE = "space"
    UP_ARROW = "up arrow"
    DOWN_ARROW = "down arrow"
    LEFT_ARROW = "left arrow"
    RIGHT_ARROW = "right arrow"
    VISIBILITY_ROW1 = "row1_visibility"
    VISIBILITY_ROW2 = "row2_visibility"
    VISIBILITY_ROW3 = "row3_visibility"
    VISIBILITY_ROW4 = "row4_visibility"
    VISIBILITY_ROW5 = "row5_visibility"
    TOGGLE_TILT_OFF = "tilt_none"
    TOGGLE_TILT_ARROWS = "tilt_arrows"
    TOGGLE_TILT_WASD = "tilt_wasd"

class KeyTypes(object):
    LISTENED_KEY = "listenedKeys"
    KEY_PRESSED_BRICK = "keyPressedBrick"
    FUNCTIONALITY_KEY = "functionalityKey"

class KeyListsAndSettings(object):
    listened_keys = []
    x_offset = -20
    y_offset = -20
    any_key_script_exists = False
    any_key_brick_exists = False
    missing_row_counter = 0
    missing_literal_columns = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    missing_num_columns = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

class KeyData(object):
    key_name = ""
    key_type = ""
    x_pos = 0
    y_pos = 0

    def __init__(self, name, type, x_pos, y_pos):
        self.key_name = name
        self.key_type = type
        self.x_pos = x_pos
        self.y_pos = y_pos

class TiltKeyData(object):
    key_name = ""
    inclination = None
    operator = None
    compare_value = 0
    active_state = 0

    def __init__(self, name, inclination, operator, value, active_state):
        self.key_name = name
        self.inclination = inclination
        self.operator = operator
        self.compare_value = value
        self.active_state = active_state

TILT_KEY_DATA = [TiltKeyData(KeyNames.UP_ARROW, catformula.Sensors.Y_INCLINATION, catformula.Operators.SMALLER_THAN, -20, 1),
                 TiltKeyData(KeyNames.DOWN_ARROW, catformula.Sensors.Y_INCLINATION, catformula.Operators.GREATER_THAN, 20, 1),
                 TiltKeyData(KeyNames.RIGHT_ARROW, catformula.Sensors.X_INCLINATION, catformula.Operators.SMALLER_THAN, -20, 1),
                 TiltKeyData(KeyNames.LEFT_ARROW, catformula.Sensors.X_INCLINATION, catformula.Operators.GREATER_THAN, 20, 1),
                 TiltKeyData("w", catformula.Sensors.Y_INCLINATION, catformula.Operators.SMALLER_THAN, -20, 2),
                 TiltKeyData("s", catformula.Sensors.Y_INCLINATION, catformula.Operators.GREATER_THAN, 20, 2),
                 TiltKeyData("d", catformula.Sensors.X_INCLINATION, catformula.Operators.SMALLER_THAN, -20, 2),
                 TiltKeyData("a", catformula.Sensors.X_INCLINATION, catformula.Operators.GREATER_THAN, 20, 2)]

KEY_NAMES_ROW_1 = [KeyNames.SPACE, KeyNames.LEFT_ARROW, KeyNames.DOWN_ARROW, KeyNames.RIGHT_ARROW, KeyNames.UP_ARROW]
KEY_NAMES_ROW_2 = ["z", "x", "c", "v", "b", "n", "m"]
KEY_NAMES_ROW_3 = ["a", "s", "d", "f", "g", "h", "j", "k", "l"]
KEY_NAMES_ROW_4 = ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"]
KEY_NAMES_ROW_5 = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]

log = logger.log

# global position variables for visible variable positioning
VISIBLE_VAR_X_INIT = -220
VISIBLE_VAR_Y_INIT = 170
VISIBLE_VAR_POSITION_STEP_X = 80
VISIBLE_VAR_POSITION_STEP_Y = 40
VISIBLE_VAR_POSITION_THRESHOLD_X = 220
VISIBLE_VAR_POSITION_THRESHOLD_Y = -20


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
    message = "key_" + key_name + "_pressed"
    return message.lower()

def _get_existing_sprite_with_name(sprite_list, name):
    for sprite in sprite_list:
        if sprite.getName() == name:
            return sprite
    return None

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

def is_supported_block(key):
    cls = _ScratchToCatrobat
    all_keys = cls.complete_mapping.keys()
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
        "10 ^": lambda value: catrobat.create_formula_element_for([catformula.Functions.POWER, 10, value]),
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
        "broadcast:": None,
        "doBroadcastAndWait": None,
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
        "contentsOfList:": None,
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
        "dragMode": None,

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
        "penColor:": None,
        "penSize:": None,
        "setPenParamTo:": None,
        "changePenSizeBy:": None,
        "changePenParamBy:": None,

        #name and number
        "sceneName": catformula.Sensors.OBJECT_BACKGROUND_NAME,
        "costumeName": catformula.Sensors.OBJECT_LOOK_NAME,
        "backgroundIndex": catformula.Sensors.OBJECT_BACKGROUND_NUMBER,
        "costumeIndex": catformula.Sensors.OBJECT_LOOK_NUMBER,

        # WORKAROUND: using ROUND for Catrobat float => Scratch int
        "soundLevel": lambda *_args: catrobat.formula_element_for(catformula.Functions.ROUND,
                                       arguments=[catrobat.formula_element_for(catformula.Sensors.LOUDNESS)]),  # @UndefinedVariable
        "note:": catbricks.NoteBrick,
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
            my_script = catbase.WhenConditionScript()
            when_cond_brick.script = my_script
            my_script.scriptBrick = when_cond_brick
            my_script.formulaMap = when_cond_brick.formulaMap
            return my_script

        if scratch_script_name == scratch.SCRIPT_WHEN_BACKGROUND_SWITCHES_TO:
            background = catrobat.background_sprite_of(catrobat_project.getDefaultScene())
            background = sprite if background is None else background
            assert catrobat.is_background_sprite(background)
            for look in background.getLookList():
                if arguments[0] == look.getName():
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
        looks = sprite.getLookList()
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

    if isinstance(unconverted_formula, int) or isinstance(unconverted_formula, float):
        formula_right_child = catformula.FormulaElement(catElementType.NUMBER, None, None)
        formula_right_child.value = str(unconverted_formula)

    else:
        test_project = catbase.Project(None, "__wct_test_project__")
        test_scene = catbase.Scene("Scene 1", test_project)
        test_project.sceneList.add(test_scene)
        tmp_block_conv = _ScratchObjectConverter(test_project, None)
        dummy = _create_catrobat_sprite_stub()
        [formula_right_child] = tmp_block_conv._catrobat_bricks_from(unconverted_formula, dummy)
        assert isinstance(formula_right_child, catformula.FormulaElement)

    traverser = _BlocksConversionTraverser(sprite, catrobat_project)
    return catformula.Formula(traverser._converted_helper_brick_or_formula_element([formula_left_child, formula_right_child], ">"))

def _create_user_brick(context, scratch_function_header, param_values, declare=False):
    # TODO: remove the next line of code as soon as user bricks are supported by Catrobat
    # TODO: also check the other TODOs related to this issue (overall three different places in converter.py)
    # TODO: refactor this function; maybe split the function into definition of user brick script and usage of the brick
    return catbricks.NoteBrick("Sorry, we currently do not support user bricks in Catrobat!")
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
            if function_header_part in {'%n', '%b'}:
                if param_value is None:
                    param_value = 0
                else:
                    param_value = int(param_value)
            else:
                if param_value is None:
                    param_value = ""
                else:
                    param_value = str(param_value)
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

def _get_or_create_shared_global_answer_variable(project):
    shared_global_answer_user_variable = project.getUserVariable(_SHARED_GLOBAL_ANSWER_VARIABLE_NAME)
    if shared_global_answer_user_variable is None:
        assert(_is_generated(_SHARED_GLOBAL_ANSWER_VARIABLE_NAME))
        catrobat.add_user_variable(project, _SHARED_GLOBAL_ANSWER_VARIABLE_NAME, None, None)
        shared_global_answer_user_variable = project.getUserVariable(_SHARED_GLOBAL_ANSWER_VARIABLE_NAME)

    assert shared_global_answer_user_variable is not None \
    and shared_global_answer_user_variable.getName() == _SHARED_GLOBAL_ANSWER_VARIABLE_NAME, \
    "variable: %s" % (_SHARED_GLOBAL_ANSWER_VARIABLE_NAME)
    return shared_global_answer_user_variable

#TODO: refactor
# TODO: refactor _key_* functions to be used just once
def _key_image_path_for(key):
    key_images_path = os.path.join(common.get_project_base_path(), 'resources', 'images', 'keys')
    for key_filename in os.listdir(key_images_path):
        basename, _ = os.path.splitext(key_filename)
        if basename.lower().endswith("_" + "_".join(key.split())):
            return os.path.join(key_images_path, key_filename)
    log.warning("Key '%s' not found in %s" % (key, os.listdir(key_images_path)))
    raise Exception("Key '%s' not found in %s" % (key, os.listdir(key_images_path)))

def _mouse_image_path():
    return os.path.join(common.get_project_base_path(), 'resources', 'images', 'keys', MOUSE_SPRITE_FILENAME)

# TODO:  refactor _key_* functions to be used just once
def _key_filename_for(key):
    assert key is not None
    key_path = _key_image_path_for(key)
    # TODO: extract method, already used once
    key_name = _key_to_broadcast_message(key).replace(" ", "_")
    _, ext =  os.path.splitext(key_path)
    return key_name + ext

def _get_mouse_filename():
    return MOUSE_SPRITE_FILENAME

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
        self.visible_var_X = VISIBLE_VAR_X_INIT
        self.visible_var_Y = VISIBLE_VAR_Y_INIT

    def add_sprite_context(self, sprite_context):
        assert isinstance(sprite_context, SpriteContext)
        self._sprite_contexts += [sprite_context]

    @property
    def sprite_contexts(self):
        return self._sprite_contexts

class SpriteContext(object):
    def __init__(self, name=None, user_script_declared_labels_map={}):
        self.name = name
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
        self.scratch_project = scratch_project

    @classmethod
    def converted_project_for(cls, scratch_project, progress_bar=None, context=None):
        converter = Converter(scratch_project)
        catrobat_project = converter._converted_catrobat_program(progress_bar, context)
        assert catrobat.is_background_sprite(catrobat_project.getDefaultScene().getSpriteList().get(0))
        return ConvertedProject(catrobat_project, scratch_project)

    def _converted_catrobat_program(self, progress_bar=None, context=None):
        scratch_project = self.scratch_project
        _catr_project = catbase.Project(None, scratch_project.name)
        _catr_scene = catbase.Scene( CATROBAT_DEFAULT_SCENE_NAME, _catr_project)
        _catr_project.sceneList.add(_catr_scene)
        _catr_scene = _catr_project.getDefaultScene()
        ProjectManager.getInstance().setCurrentProject(_catr_project)

        self._scratch_object_converter = _ScratchObjectConverter(_catr_project, scratch_project,
                                                                 progress_bar, context)
        self._add_global_user_lists_to(_catr_scene)
        self._add_converted_sprites_to(_catr_scene)
        self.scratch_project.listened_keys = self._add_key_sprites_to(_catr_scene, self.scratch_project.listened_keys)
        self.add_cursor_sprite_to(_catr_scene, context.upcoming_sprites)
        self._update_xml_header(_catr_project.getXmlHeader(), scratch_project.project_id,
                                scratch_project.name, scratch_project.instructions,
                                scratch_project.notes_and_credits)
        return _catr_project

    def _add_global_user_lists_to(self, catrobat_scene):
        if self.scratch_project.global_user_lists is None:
            return

        for global_user_list_data in self.scratch_project.global_user_lists:
            # TODO: use "visible" as soon as show/hide-formula-list-bricks are available in Catrobat => global_formula_list["visible"]
            # TODO: use "isPersistent" as soon as Catrobat supports this => global_formula_list["isPersistent"]
            global_user_list = catformula.UserList(global_user_list_data["listName"])
            catrobat_scene.project.userLists.add(global_user_list)

    def _add_converted_sprites_to(self, catrobat_scene):
        # avoid duplicate filenames -> extend with unique identifier
        duplicate_filename_set = set()
        for scratch_object in self.scratch_project.objects:
            catr_sprite = self._scratch_object_converter(scratch_object, duplicate_filename_set)
            catrobat_scene.addSprite(catr_sprite)

    def add_cursor_sprite_to(self, catrobat_scene, upcoming_sprites):
        if not MOUSE_SPRITE_NAME in upcoming_sprites and not self.scratch_project._has_mouse_position_script:
            return

        sprite = None
        if MOUSE_SPRITE_NAME in upcoming_sprites:
            sprite = upcoming_sprites[MOUSE_SPRITE_NAME]
        else:
            sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, MOUSE_SPRITE_NAME)

        look = catcommon.LookData()
        look.setName(MOUSE_SPRITE_NAME)
        mouse_filename = _get_mouse_filename()
        look.fileName = mouse_filename
        sprite.getLookList().add(look)

        if self.scratch_project._has_mouse_position_script:
            position_script = catbase.StartScript()
            forever_brick = catbricks.ForeverBrick()

            var_x_name = scratch.S2CC_POSITION_X_VARIABLE_NAME_PREFIX + MOUSE_SPRITE_NAME
            pos_x_uservariable = catformula.UserVariable(var_x_name)
            pos_x_uservariable.value = catformula.Formula(0)
            set_x_formula = catformula.Formula(catformula.FormulaElement(catElementType.SENSOR, "OBJECT_X", None))
            set_x_brick = catbricks.SetVariableBrick(set_x_formula, pos_x_uservariable)

            var_y_name = scratch.S2CC_POSITION_Y_VARIABLE_NAME_PREFIX + MOUSE_SPRITE_NAME
            pos_y_uservariable = catformula.UserVariable(var_y_name)
            pos_y_uservariable.value = catformula.Formula(0)
            set_y_formula = catformula.Formula(catformula.FormulaElement(catElementType.SENSOR, "OBJECT_Y", None))
            set_y_brick = catbricks.SetVariableBrick(set_y_formula, pos_y_uservariable)

            catrobat_scene.getProject().userVariables.add(pos_x_uservariable)
            catrobat_scene.getProject().userVariables.add(pos_y_uservariable)

            wait_brick = catbricks.WaitBrick(int(scratch.UPDATE_HELPER_VARIABLE_TIMEOUT * 1000))
            forever_brick.loopBricks.addAll([set_x_brick, set_y_brick, wait_brick])
            position_script.brickList.add(forever_brick)
            sprite.addScript(position_script)

        move_script = catbase.BroadcastScript("_mouse_move_")
        move_goto = catbricks.GoToBrick()
        move_goto.spinnerSelection = catcommon.BrickValues.GO_TO_TOUCH_POSITION
        move_script.brickList.add(move_goto)
        sprite.addScript(move_script)

        start_script = catbase.StartScript()
        transperancy_brick = catbricks.SetTransparencyBrick(99.99)
        loop_brick = catbricks.ForeverBrick()
        touch_element = catformula.FormulaElement(catElementType.SENSOR, str(catformula.Sensors.FINGER_TOUCHED), None)
        touch_formula = catformula.Formula(touch_element)

        wait_until_brick = catbricks.WaitUntilBrick(touch_formula)
        clone_self_brick = catbricks.CloneBrick()
        loop_brick.loopBricks.add(wait_until_brick)
        loop_brick.loopBricks.add(clone_self_brick)
        start_bricks = [transperancy_brick, loop_brick]
        start_script.brickList.addAll(start_bricks)
        sprite.addScript(start_script)

        clone_script = catbase.WhenClonedScript()
        clone_goto = catbricks.GoToBrick()
        clone_goto.spinnerSelection = catcommon.BrickValues.GO_TO_TOUCH_POSITION
        clone_broadcast = catbricks.BroadcastBrick("_mouse_move_")

        # workaround for touching a converted keyboard key with the converted mouse
        if len(self.scratch_project.listened_keys) > 0:
            listened_keys_names = [key_tuple[0] for key_tuple in self.scratch_project.listened_keys]
            or_formula_element = catformula.FormulaElement(catElementType.OPERATOR, str(catformula.Operators.LOGICAL_OR), None)
            colide_with_all_keys = or_formula_element.clone()
            root =  catformula.FormulaElement(catElementType.OPERATOR, str(catformula.Operators.LOGICAL_NOT), None)
            root.setRightChild(colide_with_all_keys)
            for key in listened_keys_names:
                left = catformula.FormulaElement(catElementType.COLLISION_FORMULA, _key_to_broadcast_message(key), None)
                colide_with_all_keys.setLeftChild(left)
                colide_with_all_keys.setRightChild(or_formula_element.clone())
                colide_with_all_keys.rightChild.parent = colide_with_all_keys
                colide_with_all_keys.leftChild.parent = colide_with_all_keys
                colide_with_all_keys = colide_with_all_keys.rightChild
            #the lowest layer is an or now where the left child is set but no right child. therefore we move that left child up by 1 layer
            colide_with_all_keys.parent.leftChild.parent = colide_with_all_keys.parent
            colide_with_all_keys.parent.parent.setRightChild(colide_with_all_keys.parent.leftChild)

            clone_if = catbricks.IfThenLogicBeginBrick(catformula.Formula(root))
            clone_if.ifBranchBricks.add(clone_broadcast)
            clone_bricks = [clone_goto, clone_if]
            clone_script.brickList.addAll(clone_bricks)

        else:
            clone_script.brickList.add(clone_broadcast)

        clone_kill = catbricks.DeleteThisCloneBrick()
        clone_script.brickList.add(clone_kill)
        sprite.addScript(clone_script)
        catrobat_scene.addSprite(sprite)

    # key script creating functions ------------------------------------------------------------------------------------
    @staticmethod
    def _create_or_get_user_variable(catrobat_scene, name, value):
        user_variable = catrobat_scene.project.getUserVariable(name)
        if user_variable is None:
            user_variable = catformula.UserVariable(name)
            user_variable.value = catformula.Formula(value)
            catrobat_scene.getProject().userVariables.add(user_variable)
        return user_variable

    #toggle key visibility scripts
    @staticmethod
    def visibility_workaround_for_key(key_sprite, visibility_user_variable, key_message):
        when_tapped_script = catbase.BroadcastScript(key_message)

        is_visible_formula = catrobat.create_formula_for([catformula.Operators.EQUAL, 1, visibility_user_variable])
        if_begin_brick = catbricks.IfLogicBeginBrick(is_visible_formula)
        if_begin_brick.ifBranchBricks.add(catbricks.ShowBrick())
        if_begin_brick.elseBranchBricks.add(catbricks.HideBrick())

        bricklist = [if_begin_brick]
        when_tapped_script.getBrickList().addAll(bricklist)
        key_sprite.addScript(when_tapped_script)

    #tilt sensor scripts
    @staticmethod
    def _create_when_toggle_tilt_key_tapped_script(tilt_state_variable):
        when_tapped_script = catbase.WhenScript()
        next_look_brick = catbase.bricks.NextLookBrick()

        tilt_state_is_0_formula = catrobat.create_formula_for([catformula.Operators.EQUAL, 0, tilt_state_variable])
        tilt_state_is_1_formula = catrobat.create_formula_for([catformula.Operators.EQUAL, 1, tilt_state_variable])
        set_tilt_state_to_0 = _create_variable_brick(0, tilt_state_variable, catbricks.SetVariableBrick)
        set_tilt_state_to_1 = _create_variable_brick(1, tilt_state_variable, catbricks.SetVariableBrick)
        set_tilt_state_to_2 = _create_variable_brick(2, tilt_state_variable, catbricks.SetVariableBrick)
        if_begin_brick_outer = catbricks.IfLogicBeginBrick(tilt_state_is_0_formula)
        if_begin_brick_outer.ifBranchBricks.add(set_tilt_state_to_1)
        if_begin_brick_inner = catbricks.IfLogicBeginBrick(tilt_state_is_1_formula)
        if_begin_brick_inner.ifBranchBricks.add(set_tilt_state_to_2)
        if_begin_brick_inner.elseBranchBricks.add(set_tilt_state_to_0)
        if_begin_brick_outer.elseBranchBricks.add(if_begin_brick_inner)

        when_tapped_script.brickList.addAll([next_look_brick, if_begin_brick_outer])
        return when_tapped_script

    @staticmethod
    def _create_stop_tilt_formula(tilt_state_user_variable, tilt_key_data):
        stop_operator = catformula.Operators.GREATER_THAN
        if tilt_key_data.operator is catformula.Operators.GREATER_THAN:
            stop_operator = catformula.Operators.SMALLER_THAN

        stop_tilt_expression = [catformula.Operators.LOGICAL_OR, [stop_operator, tilt_key_data.inclination, tilt_key_data.compare_value],
                                                                 [catformula.Operators.NOT_EQUAL, tilt_key_data.active_state, tilt_state_user_variable]]
        return catrobat.create_formula_for(stop_tilt_expression)

    @staticmethod
    def _create_when_tilt_script(catrobat_scene, tilt_state_user_variable, tilt_key_data):
        if_tilt_formula = catrobat.create_formula_for([tilt_key_data.operator, tilt_key_data.inclination, tilt_key_data.compare_value])
        if_tilt = catbricks.IfThenLogicBeginBrick(if_tilt_formula)

        global_key_var_name = scratch.S2CC_KEY_VARIABLE_NAME + tilt_key_data.key_name
        key_user_variable = Converter._create_or_get_user_variable(catrobat_scene, global_key_var_name, 0)
        set_tilt_active = _create_variable_brick(1, key_user_variable, catbricks.SetVariableBrick)

        key_message = _key_to_broadcast_message(tilt_key_data.key_name)
        broadcast_brick1 = catbricks.BroadcastBrick(key_message)
        wait_brick1 = catbricks.WaitBrick(250)

        stop_tilt_formula = Converter._create_stop_tilt_formula(tilt_state_user_variable, tilt_key_data)
        repeat_until_brick = catbricks.RepeatUntilBrick(stop_tilt_formula)
        broadcast_brick2 = catbricks.BroadcastBrick(key_message)
        wait_brick2 = catbricks.WaitBrick(50)
        repeat_until_brick.loopBricks.add(broadcast_brick2)
        repeat_until_brick.loopBricks.add(wait_brick2)

        set_tilt_inactive = catbricks.SetVariableBrick(catformula.Formula(0), key_user_variable)
        bricklist = [set_tilt_active, broadcast_brick1, wait_brick1, repeat_until_brick, set_tilt_inactive]
        if_tilt.ifBranchBricks.addAll(bricklist)
        return if_tilt

    #keyboard key scripts
    @staticmethod
    def _create_when_key_tapped_script(key_sprite, key_message):
        when_tapped_script = catbase.WhenScript()
        broadcast_brick1 = catbricks.BroadcastBrick(key_message)
        wait_brick1 = catbricks.WaitBrick(250)

        not_touching_formula = catrobat.create_formula_for([catformula.Operators.LOGICAL_NOT, catformula.Sensors.COLLIDES_WITH_FINGER])
        repeat_until_brick = catbricks.RepeatUntilBrick(not_touching_formula)
        broadcast_brick2 = catbricks.BroadcastBrick(key_message)
        wait_brick2 = catbricks.WaitBrick(50)
        repeat_until_brick.loopBricks.add(broadcast_brick2)
        repeat_until_brick.loopBricks.add(wait_brick2)

        bricklist = [broadcast_brick1, wait_brick1, repeat_until_brick]
        when_tapped_script.brickList.addAll(bricklist)
        key_sprite.addScript(when_tapped_script)

    @staticmethod
    def _create_when_key_pressed_script(catrobat_scene, key_sprite, key):
        when_tapped_script = catbase.WhenScript()

        global_key_var_name = scratch.S2CC_KEY_VARIABLE_NAME + key
        key_user_variable = Converter._create_or_get_user_variable(catrobat_scene, global_key_var_name, 0)

        set_variable_brick1 = _create_variable_brick(1, key_user_variable, catbricks.SetVariableBrick)
        not_touching_formula = catrobat.create_formula_for([catformula.Operators.LOGICAL_NOT, catformula.Sensors.COLLIDES_WITH_FINGER])
        wait_until_brick = catbricks.WaitUntilBrick(not_touching_formula)
        set_variable_brick2 = catbricks.SetVariableBrick(catformula.Formula(0), key_user_variable)

        bricklist = [set_variable_brick1, wait_until_brick, set_variable_brick2]
        when_tapped_script.getBrickList().addAll(bricklist)
        key_sprite.addScript(when_tapped_script)


    # key sprite creating functions ------------------------------------------------------------------------------------
    @staticmethod
    def _create_key_sprite(catrobat_scene, key_data, additional_looks = []):
        key_name = "key_" + key_data.key_name
        new_sprite = False
        key_sprite = _get_existing_sprite_with_name(catrobat_scene.getSpriteList(), key_name)
        if not key_sprite is None:
            return key_sprite, new_sprite

        key_sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, key_name)
        key_look_main = catcommon.LookData()
        key_look_main.setName(key_name)
        key_look_main.fileName = _key_filename_for(key_data.key_name)
        key_sprite.getLookList().add(key_look_main)

        for look_name in additional_looks:
            key_look = catcommon.LookData()
            key_look.setName("key_" + look_name)
            key_look.fileName = _key_filename_for(look_name)
            key_sprite.getLookList().add(key_look)

        #set looks and position via started script
        when_started_script = catbase.StartScript()
        set_look_brick = catbricks.SetLookBrick()
        set_look_brick.setLook(key_look_main)
        place_at_brick = catbricks.PlaceAtBrick(key_data.x_pos, key_data.y_pos)
        bricks = [place_at_brick, set_look_brick, catbricks.SetSizeToBrick(33)]
        when_started_script.getBrickList().addAll(bricks)
        key_sprite.addScript(when_started_script)
        catrobat_scene.addSprite(key_sprite)
        new_sprite = True

        return key_sprite, new_sprite

    @staticmethod
    def _add_toggle_tilt_key_sprite_and_scripts(catrobat_scene, key_data, tilt_key_names):
        key_sprite, add_sprite = Converter._create_key_sprite(catrobat_scene, key_data, [KeyNames.TOGGLE_TILT_ARROWS, KeyNames.TOGGLE_TILT_WASD])

        tilt_state_user_variable_name = scratch.S2CC_KEY_VARIABLE_NAME + key_data.key_name
        tilt_state_user_variable = Converter._create_or_get_user_variable(catrobat_scene, tilt_state_user_variable_name, 0)

        when_tapped_script = Converter._create_when_toggle_tilt_key_tapped_script(tilt_state_user_variable)
        key_sprite.addScript(when_tapped_script)

        listen_to_tilt_scripts = []
        for data in TILT_KEY_DATA:
            when_start_script = catbase.StartScript()
            do_forever = catbricks.ForeverBrick()

            arror_tilt_formula = catrobat.create_formula_for([catformula.Operators.EQUAL, 1, tilt_state_user_variable])
            wasd_tilt_formula = catrobat.create_formula_for([catformula.Operators.EQUAL, 2, tilt_state_user_variable])
            if_arrow_tilt_active = catbricks.IfThenLogicBeginBrick(arror_tilt_formula)
            if_wasd_tilt_active = catbricks.IfThenLogicBeginBrick(wasd_tilt_formula)
            wait_brick = catbricks.WaitBrick(50)

            if data.key_name in tilt_key_names:
                if_tilt_block = Converter._create_when_tilt_script(catrobat_scene, tilt_state_user_variable, data)
                if data.key_name in KEY_NAMES_ROW_1:
                    if_arrow_tilt_active.ifBranchBricks.add(if_tilt_block)
                else:
                    if_wasd_tilt_active.ifBranchBricks.add(if_tilt_block)

            loop_bricks = [if_arrow_tilt_active, if_wasd_tilt_active, wait_brick]
            do_forever.loopBricks.addAll(loop_bricks)
            when_start_script.brickList.addAll([do_forever])
            listen_to_tilt_scripts.append(when_start_script)

        for script in listen_to_tilt_scripts:
            key_sprite.addScript(script)

    @staticmethod
    def _add_row_visibility_sprite_and_scripts(catrobat_scene, key_data):
        key_sprite, add_sprite = Converter._create_key_sprite(catrobat_scene, key_data)

        row_visibility_user_variable_name = scratch.S2CC_KEY_VARIABLE_NAME + key_data.key_name
        row_visibility_user_variable = Converter._create_or_get_user_variable(catrobat_scene, row_visibility_user_variable_name, 1)

        when_tapped_script = catbase.WhenScript()
        broadcast_brick = catbricks.BroadcastBrick(_key_to_broadcast_message(key_data.key_name))
        wait_brick = catbricks.WaitBrick(250)

        is_visible_formula = catrobat.create_formula_for([catformula.Operators.EQUAL, 1, row_visibility_user_variable])
        if_begin_brick = catbricks.IfLogicBeginBrick(is_visible_formula)
        set_visible = _create_variable_brick(1, row_visibility_user_variable, catbricks.SetVariableBrick)
        set_invisible = _create_variable_brick(0, row_visibility_user_variable, catbricks.SetVariableBrick)
        if_begin_brick.ifBranchBricks.add(set_invisible)
        if_begin_brick.elseBranchBricks.add(set_visible)

        bricklist = [broadcast_brick, wait_brick, if_begin_brick]
        when_tapped_script.brickList.addAll(bricklist)
        key_sprite.addScript(when_tapped_script)

        return row_visibility_user_variable, _key_to_broadcast_message(key_data.key_name)

    @staticmethod
    def _add_key_sprite_and_scripts(catrobat_scene, key_data, key_lists):
        key_message = _key_to_broadcast_message(key_data.key_name)
        key_sprite, add_sprite_to_scene = Converter._create_key_sprite(catrobat_scene, key_data)

        if key_data.key_type == KeyTypes.LISTENED_KEY:
            Converter._create_when_key_tapped_script(key_sprite, key_message)
        if key_lists.any_key_script_exists:
            Converter._create_when_key_tapped_script(key_sprite, _key_to_broadcast_message(KeyNames.ANY))
        if key_data.key_type == KeyTypes.KEY_PRESSED_BRICK:
            Converter._create_when_key_pressed_script(catrobat_scene, key_sprite, key_data.key_name)
        if key_lists.any_key_brick_exists:
            Converter._create_when_key_pressed_script(catrobat_scene, key_sprite, KeyNames.ANY)

        return add_sprite_to_scene, key_sprite

    # helper functions -------------------------------------------------------------------------------------------------
    @staticmethod
    def _check_and_add_any_variants(key_lists):
        any_key_variants = [key_tuple[1] for key_tuple in key_lists.listened_keys if key_tuple[0] == KeyNames.ANY]
        key_lists.any_key_script_exists = KeyTypes.LISTENED_KEY in any_key_variants
        key_lists.any_key_brick_exists = KeyTypes.KEY_PRESSED_BRICK in any_key_variants
        key_lists.listened_keys = [key_tuple for key_tuple in key_lists.listened_keys if not key_tuple[0] == KeyNames.ANY]
        if len(any_key_variants) > 0 and len(key_lists.listened_keys) == 0:
            key_lists.listened_keys = [("a", KeyNames.ANY)]
        return key_lists

    @staticmethod
    def _listening_to_keys(keys_to_check, listened_key_names):
        keys_to_return = []
        for key in keys_to_check:
            if key in listened_key_names:
                keys_to_return.append(key)
        return keys_to_return

    @staticmethod
    def _set_toggle_tilt_key(catrobat_scene, key_lists):
        key_data = KeyData(KeyNames.TOGGLE_TILT_OFF, KeyTypes.FUNCTIONALITY_KEY, 220, -160)
        listened_key_names = [key_tuple[0] for key_tuple in key_lists.listened_keys]
        tilt_key_names = [TiltKeyData.key_name for TiltKeyData in TILT_KEY_DATA]
        tilt_key_names = Converter._listening_to_keys(tilt_key_names, listened_key_names)
        if tilt_key_names:
            Converter._add_toggle_tilt_key_sprite_and_scripts(catrobat_scene, key_data, tilt_key_names)
            key_lists.listened_keys.append((KeyNames.TOGGLE_TILT_OFF, KeyTypes.FUNCTIONALITY_KEY))
            key_lists.listened_keys.append((KeyNames.TOGGLE_TILT_ARROWS, KeyTypes.FUNCTIONALITY_KEY))
            key_lists.listened_keys.append((KeyNames.TOGGLE_TILT_WASD, KeyTypes.FUNCTIONALITY_KEY))
        return key_lists

    @staticmethod
    def _check_for_unused_keyboard_columns(key_lists):
        for key, key_type in key_lists.listened_keys:
            if key in KEY_NAMES_ROW_2 and KEY_NAMES_ROW_2.index(key) in key_lists.missing_literal_columns:
                key_lists.missing_literal_columns.remove(KEY_NAMES_ROW_2.index(key))
            elif key in KEY_NAMES_ROW_3 and KEY_NAMES_ROW_3.index(key) in key_lists.missing_literal_columns:
                key_lists.missing_literal_columns.remove(KEY_NAMES_ROW_3.index(key))
            elif key in KEY_NAMES_ROW_4 and KEY_NAMES_ROW_4.index(key) in key_lists.missing_literal_columns:
                key_lists.missing_literal_columns.remove(KEY_NAMES_ROW_4.index(key))
            elif key in KEY_NAMES_ROW_5 and KEY_NAMES_ROW_5.index(key) in key_lists.missing_num_columns:
                key_lists.missing_num_columns.remove(KEY_NAMES_ROW_5.index(key))
        return key_lists

    @staticmethod
    def _get_key_list_for_row(key_lists, row_list):
        row_keys = [key_tuple for key_tuple in key_lists.listened_keys if key_tuple[0] in row_list]
        return row_keys

    @staticmethod
    def _set_row_visibility_key(catrobat_scene, row_keys, key_lists, row_pos, row_name):
        key_data = KeyData(row_name, KeyTypes.FUNCTIONALITY_KEY, -225, row_pos)
        row_visibility_user_variable = None
        key_message = None
        if not row_keys:
            key_lists.missing_row_counter = key_lists.missing_row_counter + 1
        else:
            row_visibility_user_variable, key_message = Converter._add_row_visibility_sprite_and_scripts(catrobat_scene, key_data)
            key_lists.listened_keys.append((row_name, KeyTypes.FUNCTIONALITY_KEY))
        return key_lists, row_visibility_user_variable, key_message

    @staticmethod
    def _get_key_position(stage_size, offset, row_or_col):
        return int(-(stage_size / 2) + offset + 40 * row_or_col)

    # main key function ------------------------------------------------------------------------------------------------
    @staticmethod
    def _process_first_row(catrobat_scene, key_lists):
        row_1_keys = Converter._get_key_list_for_row(key_lists, KEY_NAMES_ROW_1)
        height_pos = 1
        y_pos = Converter._get_key_position(scratch.STAGE_HEIGHT_IN_PIXELS, key_lists.y_offset, height_pos)
        key_lists, row_visibility_user_variable, key_message = Converter._set_row_visibility_key(catrobat_scene, row_1_keys, key_lists, y_pos, KeyNames.VISIBILITY_ROW1)
        # process row one different from others
        for key, key_type in row_1_keys:
            x_pos = 0 # if space key
            y_pos = Converter._get_key_position(scratch.STAGE_HEIGHT_IN_PIXELS, key_lists.y_offset, height_pos)
            if key == KeyNames.LEFT_ARROW:
                x_pos = Converter._get_key_position(scratch.STAGE_WIDTH_IN_PIXELS, key_lists.x_offset, 9)
            elif key == KeyNames.DOWN_ARROW:
                x_pos = Converter._get_key_position(scratch.STAGE_WIDTH_IN_PIXELS, key_lists.x_offset, 10)
            elif key == KeyNames.RIGHT_ARROW:
                x_pos = Converter._get_key_position(scratch.STAGE_WIDTH_IN_PIXELS, key_lists.x_offset, 11)
            elif key == KeyNames.UP_ARROW:
                if not (len(row_1_keys) == 1):
                    y_pos = Converter._get_key_position(scratch.STAGE_HEIGHT_IN_PIXELS, key_lists.y_offset, 2)
                x_pos = Converter._get_key_position(scratch.STAGE_WIDTH_IN_PIXELS, key_lists.x_offset, 10)
            key_data = KeyData(key, key_type, x_pos, y_pos)
            add_sprite_to_scene, key_sprite = Converter._add_key_sprite_and_scripts(catrobat_scene, key_data, key_lists)
            if add_sprite_to_scene:
                Converter.visibility_workaround_for_key(key_sprite, row_visibility_user_variable, key_message)
        return key_lists

    @staticmethod
    def _process_row(key_lists, catrobat_scene, row_key_names, height_pos, width_offset, visibility_key_name):
        row_keys = Converter._get_key_list_for_row(key_lists, row_key_names)
        height_pos = height_pos - key_lists.missing_row_counter
        y_pos = Converter._get_key_position(scratch.STAGE_HEIGHT_IN_PIXELS, key_lists.y_offset, height_pos)
        key_lists, row_visibility_user_variable, key_message = Converter._set_row_visibility_key(catrobat_scene, row_keys, key_lists, y_pos, visibility_key_name)
        for key, key_type in row_keys:
            missing_columns_before_key = 0
            missing_columns = key_lists.missing_num_columns if row_key_names == KEY_NAMES_ROW_5 else key_lists.missing_literal_columns
            for index in missing_columns:
                if index < row_key_names.index(key):
                    missing_columns_before_key += 1
            width_pos = row_key_names.index(key) + width_offset - missing_columns_before_key
            x_pos = Converter._get_key_position(scratch.STAGE_WIDTH_IN_PIXELS, key_lists.x_offset, width_pos)
            key_data = KeyData(key, key_type, x_pos, y_pos)
            add_sprite_to_scene, key_sprite = Converter._add_key_sprite_and_scripts(catrobat_scene, key_data, key_lists)
            if add_sprite_to_scene:
                Converter.visibility_workaround_for_key(key_sprite, row_visibility_user_variable, key_message)
        return key_lists

    @staticmethod
    def _add_key_sprites_to(catrobat_scene, listened_keys):
        key_lists = KeyListsAndSettings()
        key_lists.listened_keys = listened_keys
        key_lists = Converter._check_and_add_any_variants(key_lists)
        key_lists = Converter._set_toggle_tilt_key(catrobat_scene, key_lists)
        key_lists = Converter._check_for_unused_keyboard_columns(key_lists)

        key_lists = Converter._process_first_row(catrobat_scene, key_lists)
        key_lists = Converter._process_row(key_lists, catrobat_scene, KEY_NAMES_ROW_2, 2, 3, KeyNames.VISIBILITY_ROW2)
        key_lists = Converter._process_row(key_lists, catrobat_scene, KEY_NAMES_ROW_3, 3, 2.5, KeyNames.VISIBILITY_ROW3)
        key_lists = Converter._process_row(key_lists, catrobat_scene, KEY_NAMES_ROW_4, 4, 2, KeyNames.VISIBILITY_ROW4)
        key_lists = Converter._process_row(key_lists, catrobat_scene, KEY_NAMES_ROW_5, 5, 2, KeyNames.VISIBILITY_ROW5)
        return key_lists.listened_keys


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
        xml_header.setProjectName('%s' % program_name) # NOTE: needed to workaround unicode issue!
        xml_header.setCatrobatLanguageVersion(catrobat.CATROBAT_LANGUAGE_VERSION)
        xml_header.setDeviceName(helpers.scratch_info("device_name"))
        xml_header.setPlatform(helpers.scratch_info("platform"))
        xml_header.setPlatformVersion(helpers.scratch_info("platform_version"))
        xml_header.setScreenMode(catcommon.ScreenModes.STRETCH)
        xml_header.mediaLicense = helpers.catrobat_info("media_license_url")
        xml_header.programLicense = helpers.catrobat_info("program_license_url")
        xml_header.applicationBuildType = helpers.application_info("build_type")
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
        _ScratchObjectConverter._scratch_project = scratch_project
        self._progress_bar = progress_bar
        self._context = context

    def __call__(self, scratch_object, duplicate_filename_set):
        return self._catrobat_sprite_from(scratch_object, duplicate_filename_set)

    def _catrobat_sprite_from(self, scratch_object, duplicate_filename_set):
        if not isinstance(scratch_object, scratch.Object):
            raise common.ScratchtobatError("Input must be of type={}, but is={}".format(scratch.Object, type(scratch_object)))
        sprite_name = scratch_object.name
        scratch_user_scripts = filter(lambda s: s.type == scratch.SCRIPT_PROC_DEF, scratch_object.scripts)
        scratch_user_script_declared_labels_map = dict(map(lambda s: (s.arguments[0], s.arguments[1]), scratch_user_scripts))
        sprite_context = SpriteContext(sprite_name, scratch_user_script_declared_labels_map)
        catrobat_scene = self._catrobat_project.getDefaultScene()
        sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, sprite_name)
        assert sprite_name == sprite.getName()

        if self._context is not None:
            sprite_context.context = self._context
            if sprite_name in self._context.upcoming_sprites:
                sprite = self._context.upcoming_sprites[sprite_name]

        log.info('-'*80)
        log.info("Converting Sprite: '%s'", sprite_name)
        log.info('-'*80)

        # rename if sprite is background
        if scratch_object.is_stage():
            catrobat.set_as_background(sprite)
            sprite_context.name = sprite.getName()

        # looks and sounds has to added first because of cross-validations
        sprite_looks = sprite.getLookList()
        costume_resolution = None
        for scratch_costume in scratch_object.get_costumes():
            current_costume_resolution = scratch_costume.get(scratchkeys.COSTUME_RESOLUTION)
            if not costume_resolution:
                costume_resolution = current_costume_resolution
            elif current_costume_resolution != costume_resolution:
                log.warning("Costume resolution not same for all costumes")
            sprite_looks.add(self._catrobat_look_from(scratch_costume, duplicate_filename_set))
        sprite_sounds = sprite.getSoundList()
        for scratch_sound in scratch_object.get_sounds():
            sprite_sounds.add(self._catrobat_sound_from(scratch_sound, duplicate_filename_set))

        if not scratch_object.is_stage() and scratch_object.get_lists() is not None:
            for user_list_data in scratch_object.get_lists():
                assert len(user_list_data["listName"]) > 0
                user_list = catformula.UserList(user_list_data["listName"])
                sprite.userLists.add(user_list)
                # TODO: check if user list has been added...

        for scratch_variable in scratch_object.get_variables():
            variable_name = scratch_variable["name"]
            user_variable = catrobat.add_user_variable(
                    self._catrobat_project,
                    variable_name,
                    sprite=sprite,
                    sprite_name=sprite.getName() if not scratch_object.is_stage() else None
            )
            assert user_variable is not None
            user_variable = self._catrobat_project.getUserVariable(variable_name) if scratch_object.is_stage() else sprite.getUserVariable(variable_name)

            assert user_variable is not None

        for scratch_script in scratch_object.scripts:
            cat_instance = self._catrobat_script_from(scratch_script, sprite, self._catrobat_project,
                                                      sprite_context)
            # TODO: remove this if and replace "elif" with "if" as soon as user bricks are supported by Catrobat
            # TODO: also check the other TODOs related to this issue (overall three different places in converter.py)
            if isinstance(cat_instance, catbricks.NoteBrick):
                continue
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
            self._add_default_behaviour_to(sprite, sprite_context, catrobat_scene,
                                           self._catrobat_project, scratch_object,
                                           self._scratch_project, costume_resolution)
        except Exception, e:
            log.error("exception: " + str(e))
            log.error("Cannot add default behaviour to sprite object {}".format(sprite_name))

        log.info('')
        return sprite

    @staticmethod
    def _catrobat_look_from(scratch_costume, duplicate_filename_set):
        if not scratch_costume or not (isinstance(scratch_costume, dict) and all(_ in scratch_costume for _ in (scratchkeys.COSTUME_MD5, scratchkeys.COSTUME_NAME))):
            raise common.ScratchtobatError("Wrong input, must be costume dict: {}".format(scratch_costume))
        look = catcommon.LookData()

        assert scratchkeys.COSTUME_NAME in scratch_costume
        costume_name = scratch_costume[scratchkeys.COSTUME_NAME]
        look.setName(costume_name)

        assert scratchkeys.COSTUME_MD5 in scratch_costume
        costume_md5_filename = scratch_costume[scratchkeys.COSTUME_MD5]
        look.fileName = helpers.create_catrobat_md5_filename(costume_md5_filename, duplicate_filename_set)
        return look

    @staticmethod
    def _catrobat_sound_from(scratch_sound, duplicate_filename_set):
        soundinfo = catcommon.SoundInfo()

        assert scratchkeys.SOUND_NAME in scratch_sound
        sound_name = scratch_sound[scratchkeys.SOUND_NAME]
        soundinfo.setName(sound_name)

        assert scratchkeys.SOUND_MD5 in scratch_sound
        sound_md5_filename = scratch_sound[scratchkeys.SOUND_MD5]
        soundinfo.fileName = helpers.create_catrobat_md5_filename(sound_md5_filename, duplicate_filename_set)
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
                catr_user_list = catrobat.find_global_user_list_by_name(catrobat_project, list_name)
                if "contents" not in global_user_list_data:
                    continue
                for value in global_user_list_data["contents"]:
                    catr_value_formula = catrobat.create_formula_with_value(value)
                    add_item_to_list_brick = catbricks.AddItemToUserListBrick(catr_value_formula)
                    add_item_to_list_brick.setUserList(catr_user_list)
                    implicit_bricks_to_add += [add_item_to_list_brick]

        if not scratch_object.is_stage() and scratch_object.get_lists() is not None:
            for user_list_data in scratch_object.get_lists():
                list_name = user_list_data["listName"]
                assert len(list_name) > 0
                catr_user_list = catrobat.find_sprite_user_list_by_name(sprite, list_name)
                assert catr_user_list
                if "contents" not in user_list_data:
                    continue
                for value in user_list_data["contents"]:
                    catr_value_formula = catrobat.create_formula_with_value(value)
                    add_item_to_list_brick = catbricks.AddItemToUserListBrick(catr_value_formula)
                    add_item_to_list_brick.setUserList(catr_user_list)
                    implicit_bricks_to_add += [add_item_to_list_brick]

        # object's currentCostumeIndex determines active costume at startup
        sprite_startup_look_idx = scratch_object.get_currentCostumeIndex()
        if sprite_startup_look_idx is not None:
            if isinstance(sprite_startup_look_idx, float):
                sprite_startup_look_idx = int(round(sprite_startup_look_idx))
            if sprite_startup_look_idx != 0:
                spriteStartupLook = sprite.getLookList()[sprite_startup_look_idx]
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
            object_scale = object_relative_scale * 100.0
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
        shared_global_answer_user_variable = catrobat_scene.project.getUserVariable(_SHARED_GLOBAL_ANSWER_VARIABLE_NAME)
        if shared_global_answer_user_variable is not None and scratch_object.is_stage():
            try:
                _assign_initialization_value_to_user_variable(catrobat_scene, _SHARED_GLOBAL_ANSWER_VARIABLE_NAME, "", sprite)
            except:
                log.error("Cannot assign initialization value {} to shared global answer user variable"
                          .format(_SHARED_GLOBAL_ANSWER_VARIABLE_NAME))

        # Add ShowVariable Bricks for variables that are visible
        #       (also for "answer", i.e. _SHARED_GLOBAL_ANSWER_VARIABLE_NAME!!)
        sprite_name = sprite.getName()
        sprite_name = sprite_name.replace(BACKGROUND_LOCALIZED_GERMAN_NAME, BACKGROUND_ORIGINAL_NAME)
        if not(sprite_name in scratch_project.sprite_variables_map): return
        local_sprite_variables = scratch_project.sprite_variables_map[sprite_name]
        context = sprite_context.context
        if context is None: return

        # Display visible variables at start
        for variable_name in sorted(local_sprite_variables):
            user_variable = catrobat_project.getUserVariable(variable_name) if sprite_name == "Stage" else sprite.getUserVariable(variable_name)
            show_variable_brick = catbricks.ShowTextBrick(context.visible_var_X, context.visible_var_Y)
            show_variable_brick.setUserVariable(user_variable)
            context.visible_var_Y -= VISIBLE_VAR_POSITION_STEP_Y
            if context.visible_var_Y <= VISIBLE_VAR_POSITION_THRESHOLD_Y:
                context.visible_var_Y = VISIBLE_VAR_Y_INIT
                context.visible_var_X += VISIBLE_VAR_POSITION_STEP_X
            if context.visible_var_X >= VISIBLE_VAR_POSITION_THRESHOLD_X:
                log.info("Too many visible variables")
            catrobat.add_to_start_script([show_variable_brick], sprite)

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
            cat_instance.brickList.add(_placeholder_for_unmapped_blocks_to("UNSUPPORTED SCRIPT", scratch_script.type))

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
                # TODO: remove this if and replace "elif" with "if" as soon as user bricks are supported by Catrobat
                # TODO: also check the other TODOs related to this issue (overall three different places in converter.py)
                if isinstance(cat_instance, catbricks.NoteBrick):
                    continue
                elif not isinstance(cat_instance, catbricks.UserBrick):
                    assert isinstance(cat_instance, catbase.Script)
                    cat_instance.brickList.add(brick)
                else:
                    cat_instance.appendBrickToScript(brick)
            except TypeError as ex:
                if isinstance(brick, (str, unicode)):
                    log.error("string brick: %s", brick)
                else:
                    log.error("type: %s, exception: %s", brick.__class__.__name__, ex.message)
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
        self.name = self.catrobat_program.getXmlHeader().getProjectName()

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
            storage_handler = catio.XstreamSerializer.getInstance()
            code_xml_content = storage_handler.XML_HEADER
            code_xml_content += storage_handler.xstream.toXML(catrobat_program)
            return code_xml_content

        def write_program_source(catrobat_program, context):
            program_source = program_source_for(catrobat_program)
            with open(os.path.join(temp_path, catrobat.PROGRAM_SOURCE_FILE_NAME), "wb") as fp:
                fp.write(program_source.encode("utf8"))

            # copying key images needed for keyPressed substitution
            for listened_key_tuple in self.scratch_project.listened_keys:
                try:
                    key_image_path = _key_image_path_for(listened_key_tuple[0])
                except:
                    continue

                shutil.copyfile(key_image_path, os.path.join(images_path, _key_filename_for(listened_key_tuple[0])))
            for sprite in catrobat_program.getDefaultScene().spriteList:
                if sprite.name == MOUSE_SPRITE_NAME:
                    mouse_img_path = _mouse_image_path()
                    shutil.copyfile(mouse_img_path, os.path.join(images_path, _get_mouse_filename()))

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
    user_variable = sprite.getUserVariable(variable_name) if sprite.name != BACKGROUND_LOCALIZED_GERMAN_NAME else scene.project.getUserVariable(variable_name)
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
                        converted_args = [(common.int_or_float(arg) or arg if isinstance(arg, (str, unicode)) else arg) for arg in self.arguments]
                    elif try_number == 1:
                        def handleBoolean(arg):
                            if isinstance(arg, bool):
                                return int(arg)
                            else:
                                return arg

                        converted_args = [catformula.FormulaElement(catElementType.NUMBER, str(handleBoolean(arg)), None) if isinstance(arg, numbers.Number) else arg for arg in converted_args]  # @UndefinedVariable
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

    @_register_handler(_block_name_to_handler_map, "contentsOfList:")
    def _convert_contents_of_list_block(self):
        list_name = self.arguments[0]
        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.scene, self.sprite, list_name)
        assert user_list is not None
        list_formula_element = catformula.FormulaElement(catElementType.USER_LIST, list_name, None)
        return list_formula_element

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
            if nested_bricks == None:
                nested_bricks = []
            catr_loop_start_brick = self.CatrobatClass(catrobat.create_formula_with_value(times_value))
            for brick in nested_bricks:
                catr_loop_start_brick.loopBricks.add(brick)
        else:
            assert self.block_name == 'doForever', self.block_name
            [nested_bricks] = brick_arguments
            if nested_bricks == None:
                nested_bricks = []
            catr_loop_start_brick = self.CatrobatClass()
            for brick in nested_bricks:
                catr_loop_start_brick.loopBricks.add(brick)
        return [catr_loop_start_brick]

    @_register_handler(_block_name_to_handler_map, "doUntil")
    def _convert_do_until_block(self):
        condition, nested_bricks = self.arguments
        if nested_bricks == None:
            nested_bricks = []
        repeat_until_brick = self.CatrobatClass(catrobat.create_formula_with_value(condition))
        for brick in nested_bricks:
            repeat_until_brick.loopBricks.add(brick)
        return repeat_until_brick

    @_register_handler(_block_name_to_handler_map, "startScene")
    def _convert_scene_block(self):
        [argument] = self.arguments

        background_sprite = catrobat.background_sprite_of(self.scene)

        if not background_sprite:
            assert catrobat.is_background_sprite(self.sprite)
            background_sprite = self.sprite

        if isinstance(argument, (catformula.FormulaElement, int, float)):
            value = argument if not isinstance(argument, float) else int(argument)
            #=========================================================================
            # wrap around overflow correction term:
            #=========================================================================
            # 1st step: compute (value - 1) -> result may be out of bounds!
            index_formula_elem = self._converted_helper_brick_or_formula_element([value, 1], "-")
            # 2nd step: consider overflow, i.e. ((value - 1) % number_of_looks)
            #           -> now, the result cannot be out of bounds any more!
            number_of_looks = len(background_sprite.getLookList())
            assert number_of_looks > 0
            index_formula_elem = self._converted_helper_brick_or_formula_element([index_formula_elem, number_of_looks], "%")
            # 3rd step: determine look number, i.e. (((value - 1) % number_of_looks) + 1)
            index_formula_elem = self._converted_helper_brick_or_formula_element([index_formula_elem, 1], "+")
            index_formula_elem = index_formula_elem if number_of_looks != 1 else 1
            set_background_by_index_brick = catbricks.SetBackgroundByIndexBrick(catrobat.create_formula_with_value(index_formula_elem))
            return set_background_by_index_brick

        look_name = argument
        if look_name in {"next backdrop", "previous backdrop"}:
            index_formula_elem = self._converted_helper_brick_or_formula_element([], "backgroundIndex")
            if look_name == "next backdrop":
                if catrobat.is_background_sprite(self.sprite):
                    return catbricks.NextLookBrick()
                index_formula_elem = self._converted_helper_brick_or_formula_element([index_formula_elem, 1], "+")
            else:
                if catrobat.is_background_sprite(self.sprite):
                    return catbricks.PreviousLookBrick()
                index_formula_elem = self._converted_helper_brick_or_formula_element([index_formula_elem, 1], "-")
            set_background_by_index_brick = catbricks.SetBackgroundByIndexBrick(catrobat.create_formula_with_value(index_formula_elem))
            return set_background_by_index_brick

        matching_looks = [_ for _ in background_sprite.getLookList() if _.getName() == look_name]
        if not matching_looks:
            errormessage = "Background does not contain look with name: {}".format(look_name)
            log.warning(errormessage)
            return catbricks.NoteBrick(errormessage)

        assert len(matching_looks) == 1

        switch_background_brick = self.CatrobatClass()
        switch_background_brick.setLook(matching_looks[0])
        return switch_background_brick

    @_register_handler(_block_name_to_handler_map, "startSceneAndWait")
    def _convert_scene_and_wait_block(self):
        [argument] = self.arguments
        assert catrobat.is_background_sprite(self.sprite), 'The ["startSceneAndWait"] block can only be used ' \
                                                           'within the stage/background object!'

        if isinstance(argument, (catformula.FormulaElement, int, float)):
            value = argument if not isinstance(argument, float) else int(argument)
            #=========================================================================
            # wrap around overflow correction term:
            #=========================================================================
            # 1st step: compute (value - 1) -> result may be out of bounds!
            index_formula_elem = self._converted_helper_brick_or_formula_element([value, 1], "-")
            # 2nd step: consider overflow, i.e. ((value - 1) % number_of_looks)
            #           -> now, the result cannot be out of bounds any more!
            number_of_looks = len(self.sprite.getLookList())
            assert number_of_looks > 0
            index_formula_elem = self._converted_helper_brick_or_formula_element([value, number_of_looks], "%")
            # 3rd step: determine look number, i.e. (((value - 1) % number_of_looks) + 1)
            index_formula_elem = self._converted_helper_brick_or_formula_element([index_formula_elem, 1], "+")
            index_formula_elem = index_formula_elem if number_of_looks != 1 else 1
            set_background_by_index_and_wait_brick = catbricks.SetBackgroundByIndexAndWaitBrick(catrobat.create_formula_with_value(index_formula_elem))
            return set_background_by_index_and_wait_brick

        look_name = argument
        if look_name == "next backdrop":
            return catbricks.NextLookBrick()
        if look_name == "previous backdrop":
            return catbricks.PreviousLookBrick()

        matching_looks = [_ for _ in self.sprite.getLookList() if _.getName() == look_name]
        if not matching_looks:
            errormessage = "Background does not contain look with name: {}".format(look_name)
            log.warning(errormessage)
            return catbricks.NoteBrick(errormessage)

        assert len(matching_looks) == 1

        switch_background_brick = self.CatrobatClass()
        switch_background_brick.setLook(matching_looks[0])
        return switch_background_brick

    #returns workaround script for sprites that are draggable at some point. Add workaround only once per sprite.
    def  _drag_mode_workaround(self, draggable_var):
        DRAG_NAME_PREFIX = "drag"
        first_set_bricks = []
        loop_start_set_bricks = []
        loop_end_set_bricks = []
        change_bricks = []

        for coord in ['x', 'y']:
            drag_stage = catrobat.add_user_variable(self.project, DRAG_NAME_PREFIX + '_stage_' + coord, self.sprite, self.sprite.getName())
            drag_stage_fe = _variable_for(drag_stage.name)
            drag_stage_new = catrobat.add_user_variable(self.project, DRAG_NAME_PREFIX + '_stage_new_' + coord, self.sprite, self.sprite.getName())
            drag_stage_new_fe = _variable_for(drag_stage_new.name)
            drag_pos = catrobat.add_user_variable(self.project, DRAG_NAME_PREFIX + '_pos_' + coord, self.sprite, self.sprite.getName())
            drag_pos_fe = _variable_for(drag_pos.name)
            drag_pos_new = catrobat.add_user_variable(self.project, DRAG_NAME_PREFIX + '_pos_new_' + coord, self.sprite, self.sprite.getName())
            drag_pos_new_fe = _variable_for(drag_pos_new.name)

            finger_fe = catformula.FormulaElement(catElementType.SENSOR, str(catformula.Sensors.FINGER_X if coord == 'x' else catformula.Sensors.FINGER_Y), None)
            object_fe = catformula.FormulaElement(catElementType.SENSOR, str(catformula.Sensors.OBJECT_X if coord == 'x' else catformula.Sensors.OBJECT_Y), None)

            first_set_bricks.append(_create_variable_brick(finger_fe, drag_stage, catbricks.SetVariableBrick))
            first_set_bricks.append(_create_variable_brick(object_fe, drag_pos, catbricks.SetVariableBrick))

            loop_start_set_bricks.append(_create_variable_brick(finger_fe, drag_stage_new, catbricks.SetVariableBrick))
            loop_start_set_bricks.append(_create_variable_brick(object_fe, drag_pos_new, catbricks.SetVariableBrick))
            move_fe = catformula.FormulaElement(catElementType.OPERATOR, str(catformula.Operators.PLUS), None)
            move_pos_diff = catformula.FormulaElement(catElementType.OPERATOR, str(catformula.Operators.MINUS), None)
            move_pos_diff.setLeftChild(drag_pos_fe)
            move_pos_diff.setRightChild(drag_pos_new_fe)
            move_fe.setLeftChild(move_pos_diff)
            move_stage_diff = catformula.FormulaElement(catElementType.OPERATOR, str(catformula.Operators.MINUS), None)
            move_stage_diff.setLeftChild(drag_stage_new_fe)
            move_stage_diff.setRightChild(drag_stage_fe)
            move_fe.setRightChild(move_stage_diff)
            change_bricks.append((catbricks.ChangeXByNBrick if coord == 'x' else catbricks.ChangeYByNBrick)(catformula.Formula(move_fe)))

            loop_end_set_bricks.append(_create_variable_brick(drag_stage_new_fe, drag_stage, catbricks.SetVariableBrick))
            loop_end_set_bricks.append(_create_variable_brick(object_fe, drag_pos, catbricks.SetVariableBrick))

        when_tapped_script = catbase.WhenScript()
        draggable_var_fe = catformula.FormulaElement(catElementType.USER_VARIABLE, draggable_var.name, None)
        if_draggable_brick = catbricks.IfThenLogicBeginBrick(catformula.Formula(draggable_var_fe))

        not_touching_fe = catformula.FormulaElement(catElementType.OPERATOR, str(catformula.Operators.LOGICAL_NOT), None)
        touching_fe = catformula.FormulaElement(catElementType.SENSOR, str(catformula.Sensors.FINGER_TOUCHED), None)
        not_touching_fe.setRightChild(touching_fe)
        repeat_until_brick = catbricks.RepeatUntilBrick(catformula.Formula(not_touching_fe))

        wait_brick = catbricks.WaitBrick(5)
        repeat_until_brick.loopBricks.addAll(loop_start_set_bricks)
        repeat_until_brick.loopBricks.addAll(change_bricks)
        repeat_until_brick.loopBricks.addAll(loop_end_set_bricks)
        repeat_until_brick.loopBricks.add(wait_brick)

        if_draggable_brick.ifBranchBricks.addAll(first_set_bricks)
        if_draggable_brick.ifBranchBricks.add(repeat_until_brick)

        when_tapped_script.brickList.add(if_draggable_brick)
        return when_tapped_script

    #replaces set_drag_mode blocks with set user variable "draggable" blocks. Injects workaround script for current sprite if not already added.
    @_register_handler(_block_name_to_handler_map, "dragMode")
    def _convert_drag_mode(self):
        assert len(self.arguments) == 1
        assert self.arguments[0] in {'draggable', 'not draggable'}
        draggable_var_name = 'draggable'
        draggable_var = self.sprite.getUserVariable(draggable_var_name)
        if not draggable_var:
            draggable_var = catrobat.add_user_variable(self.project, draggable_var_name, self.sprite, self.sprite.getName())
            self.sprite.addScript(self._drag_mode_workaround(draggable_var))
        draggable_fe = catformula.FormulaElement(catElementType.FUNCTION, str(catformula.Functions.TRUE if self.arguments[0] == "draggable" else catformula.Functions.FALSE), None)
        set_brick = _create_variable_brick(draggable_fe, draggable_var, catbricks.SetVariableBrick)
        return [set_brick]

    @_register_handler(_block_name_to_handler_map, "doIf")
    def _convert_if_block(self):
        assert len(self.arguments) == 2
        if_begin_brick = catbricks.IfThenLogicBeginBrick(catrobat.create_formula_with_value(self.arguments[0]))
        if_bricks = self.arguments[1] or []
        assert isinstance(if_bricks, list)

        for brick in if_bricks:
            if_begin_brick.ifBranchBricks.add(brick)
        return [if_begin_brick]

    @_register_handler(_block_name_to_handler_map, "doIfElse")
    def _convert_if_else_block(self):
        assert len(self.arguments) == 3
        if_begin_brick = catbricks.IfLogicBeginBrick(catrobat.create_formula_with_value(self.arguments[0]))
        if_bricks, [else_bricks] = self.arguments[1], self.arguments[2:] or [[]]
        if_bricks = if_bricks if if_bricks != None else []
        else_bricks = else_bricks if else_bricks != None else []
        for brick in if_bricks:
            if_begin_brick.ifBranchBricks.add(brick)
        for brick in else_bricks:
            if_begin_brick.elseBranchBricks.add(brick)
        return if_begin_brick

    @_register_handler(_block_name_to_handler_map, "lookLike:")
    def _convert_look_block(self):
        set_look_brick = self.CatrobatClass()
        [argument] = self.arguments

        if isinstance(argument, (catformula.FormulaElement, int, float)):
            value = argument if not isinstance(argument, float) else int(argument)
            #=========================================================================
            # wrap around overflow correction term:
            #=========================================================================
            # 1st step: compute (value - 1) -> result may be out of bounds!
            index_formula_elem = self._converted_helper_brick_or_formula_element([value, 1], "-")
            # 2nd step: consider overflow, i.e. ((value - 1) % number_of_looks)
            #           -> now, the result cannot be out of bounds any more!
            number_of_looks = len(self.sprite.getLookList())
            assert number_of_looks > 0
            index_formula_elem = self._converted_helper_brick_or_formula_element([index_formula_elem, number_of_looks], "%")
            # 3rd step: determine look number, i.e. (((value - 1) % number_of_looks) + 1)
            index_formula_elem = self._converted_helper_brick_or_formula_element([index_formula_elem, 1], "+")
            index_formula_elem = index_formula_elem if number_of_looks != 1 else 1
            return catbricks.SetLookByIndexBrick(catrobat.create_formula_with_value(index_formula_elem))

        look_name = argument
        assert isinstance(look_name, (str, unicode)), type(look_name)
        look = next((look for look in self.sprite.getLookList() if look.getName() == look_name), None)
        if look is None:
            errormessage = "Look name: '%s' not found in sprite '%s'. Available looks: %s replacing Brick with NoteBrick" % (look_name, self.sprite.getName(), ", ".join([look.getName() for look in self.sprite.getLookList()]))
            log.warning(errormessage)
            set_look_brick = catbricks.NoteBrick(errormessage)
            return set_look_brick

        set_look_brick.setLook(look)
        return set_look_brick

    @_register_handler(_block_name_to_handler_map, "showVariable:")
    def _convert_show_variable_block(self):
        [variable_name] = self.arguments
        user_variable = self.sprite.getUserVariable(variable_name)
        assert user_variable is not None # the variable must exist at this stage!
        assert user_variable.getName() == variable_name
        show_variable_brick = self.CatrobatClass(0, 0)
        #show_variable_brick.setUserVariableName(variable_name)
        show_variable_brick.setUserVariable(user_variable)
        return show_variable_brick

    @_register_handler(_block_name_to_handler_map, "hideVariable:")
    def _convert_hide_variable_block(self):
        [variable_name] = self.arguments
        user_variable = self.sprite.getUserVariable(variable_name)
        assert user_variable is not None # the variable must exist at this stage!
        assert user_variable.getName() == variable_name
        hide_variable_brick = self.CatrobatClass()
        #hide_variable_brick.setUserVariable(variable_name)
        hide_variable_brick.setUserVariable(user_variable)
        return hide_variable_brick

    @_register_handler(_block_name_to_handler_map, "append:toList:")
    def _convert_append_to_list_block(self):
        [value, list_name] = self.arguments
        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.scene, self.sprite, list_name)
        assert user_list is not None
        value_formula = catrobat.create_formula_with_value(value)
        addItemToUserListBrick = self.CatrobatClass(value_formula)
        addItemToUserListBrick.setUserList(user_list)
        return addItemToUserListBrick

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
        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.scene, self.sprite, list_name)
        assert user_list is not None
        deleteItemBrick = self.CatrobatClass()
        deleteItemBrick.userList = user_list

        if position == "last":
            index_formula = catrobat.create_formula_with_value(self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:"))
            assert index_formula is not None
            deleteItemBrick.setFormulaWithBrickField(catbricks.Brick.BrickField.LIST_DELETE_ITEM, index_formula)

            return deleteItemBrick
        if position == "all":
            loop_condition_formula = catrobat.create_formula_with_value(self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:"))
            catr_loop_start_brick = catbricks.RepeatBrick(loop_condition_formula)

            index_formula = catrobat.create_formula_with_value("1") # first item to be deleted for n-times!
            assert index_formula is not None
            deleteItemBrick.setFormulaWithBrickField(catbricks.Brick.BrickField.LIST_DELETE_ITEM, index_formula)
            catr_loop_start_brick.loopBricks.add(deleteItemBrick)

            return catr_loop_start_brick

        index_formula = catrobat.create_formula_with_value(position)
        assert index_formula is not None
        deleteItemBrick.setFormulaWithBrickField(catbricks.Brick.BrickField.LIST_DELETE_ITEM, index_formula)

        return deleteItemBrick

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

    @_register_handler(_block_name_to_handler_map, "playSound:", "doPlaySoundAndWait")
    def _convert_sound_block(self):
        [sound_parameter], sound_list = self.arguments, self.sprite.getSoundList()
        sound_data = {sound_info.getName(): sound_info for sound_info in sound_list}.get(sound_parameter)

        # while scratch allows strings and numbers as parameter for the "play sound"-bricks
        # pocket code has only the drop down menu for sound selection
        # until pocket code does not support custom parameters for these bricks the converter selects the first
        # sound in the list, if available
        if len(sound_list) == 0:
            log.warning("The sound list is empty! No sound will be played with this brick!")
        elif isinstance(sound_parameter, catformula.FormulaElement):
            log.warning("Pocket code does not support formulas or variables as input for the \"play sound\"-bricks. "\
                        "Using the first sound in the sound list instead!")
            sound_data = sound_list[0]
        elif isinstance(sound_parameter, unicode) and not sound_data:
            log.warning("Sprite does not contain sound with name=\"{}\". ".format(sound_parameter) + \
                        "Using the first sound in the sound list instead!")
            sound_data = sound_list[0]

        play_sound_brick = self.CatrobatClass()
        play_sound_brick.setSound(sound_data)
        return play_sound_brick

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
                
        # try to access a local variable with the given name
        # if no local variable is found, a global variable is referenced
        user_variable = self.sprite.getUserVariable(variable_name)
        if user_variable is None:
            user_variable = self.project.getUserVariable(variable_name)

        assert user_variable is not None and user_variable.getName() == variable_name, \
               "variable: %s, sprite_name: %s" % (variable_name, self.sprite.getName())
        return [self.CatrobatClass(value, user_variable)]

    @_register_handler(_block_name_to_handler_map, "say:duration:elapsed:from:")
    def _convert_say_duration_elapsed_from_block(self):
        [msg, duration] = self.arguments
        say_for_bubble_brick = self.CatrobatClass()
        say_for_bubble_brick.setFormulaWithBrickField(catbricks.Brick.BrickField.STRING, catformula.Formula(msg))
        say_for_bubble_brick.setFormulaWithBrickField(catbricks.Brick.BrickField.DURATION_IN_SECONDS, catformula.Formula(duration))
        return say_for_bubble_brick

    @_register_handler(_block_name_to_handler_map, "say:")
    def _convert_say_block(self):
        [msg] = self.arguments
        say_bubble_brick = self.CatrobatClass()
        say_bubble_brick.setFormulaWithBrickField(catbricks.Brick.BrickField.STRING, catformula.Formula(msg))

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
        think_bubble_brick.setFormulaWithBrickField(catbricks.Brick.BrickField.STRING, catformula.Formula(msg))
        return think_bubble_brick

    @_register_handler(_block_name_to_handler_map, "doAsk")
    def _convert_do_ask_block(self):
        [question] = self.arguments
        question_formula = catrobat.create_formula_with_value(question)
        shared_global_answer_user_variable = _get_or_create_shared_global_answer_variable(self.project)
        return self.CatrobatClass(question_formula, shared_global_answer_user_variable)

    @_register_handler(_block_name_to_handler_map, "answer")
    def _convert_answer_block(self):
        shared_global_answer_user_variable = _get_or_create_shared_global_answer_variable(self.project)
        return _variable_for(shared_global_answer_user_variable.getName())

    @_register_handler(_block_name_to_handler_map, "createCloneOf")
    def _convert_create_clone_of_block(self):
        [base_sprite] = self.arguments
        if isinstance(base_sprite, catformula.FormulaElement):
            return catbricks.NoteBrick("Can't convert Clone-Brick with Formula as argument.")

        if len(base_sprite) == 0:
            return catbricks.NoteBrick("Can't convert Clone-Brick with no argument.")

        if base_sprite == "_myself_" or base_sprite == self.sprite.getName():
            cloneSelfBrick = self.CatrobatClass()
            cloneSelfBrick.objectToClone = self.sprite
            return cloneSelfBrick

        if isinstance(base_sprite, basestring):
            for sprite in self.scene.spriteList:
                if sprite.getName() == base_sprite:
                    cloneBrick = self.CatrobatClass()
                    cloneBrick.objectToClone = sprite
                    return cloneBrick
            if base_sprite in self.script_context.sprite_context.context.upcoming_sprites:
                new_sprite = self.script_context.sprite_context.context.upcoming_sprites[base_sprite]
            else:
                new_sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, base_sprite)
                self.script_context.sprite_context.context.upcoming_sprites[new_sprite.getName()] = new_sprite

            create_clone_of_brick = self.CatrobatClass()
            create_clone_of_brick.objectToClone = new_sprite
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

    # TODO: as soon as user bricks are supported again, outsource this -
    # into a workaround by adding a user brick with this functionality to default behavior or scratch.py when needed
    # see https://de.wikipedia.org/wiki/HSV-Farbraum for the conversion formula, with 0 <= h, s, v <= 1 in our case
    def _add_hsv_to_rgb_conversion_algorithm_bricks(self):
        var = {}

        def var_id(variable_name):
            return catrobat.build_var_id(var[variable_name])

        def var_obj(variable_name):
            return self.sprite.getUserVariable(var[variable_name])

        for key, variable_name in scratch.S2CC_PEN_COLOR_HELPER_VARIABLE_NAMES.items() + \
                                  scratch.S2CC_PEN_COLOR_VARIABLE_NAMES.items():
            assert isinstance(self.sprite.getUserVariable(variable_name), catformula.UserVariable)
            var[key] = variable_name

        formula = catrobat.create_formula_for(
            [catformula.Functions.FLOOR, [catformula.Operators.MULT, var_id('h'), 6]])
        set_h_i_brick = catbricks.SetVariableBrick(formula, var_obj('h_i'))

        formula = catrobat.create_formula_for(
                [catformula.Operators.MINUS, [catformula.Operators.MULT, var_id('h'), 6], var_id('h_i')])
        set_f_brick = catbricks.SetVariableBrick(formula, var_obj('f'))

        formula = catrobat.create_formula_for(
            [catformula.Operators.MULT, var_id('v'), ["()", [catformula.Operators.MINUS, 1, var_id('s')]]])
        set_p_brick = catbricks.SetVariableBrick(formula, var_obj('p'))

        formula = catrobat.create_formula_for(
            [catformula.Operators.MULT,
                var_id('v'),
                ["()", [catformula.Operators.MINUS, 1, [catformula.Operators.MULT, var_id('s'), var_id('f')]]]])
        set_q_brick = catbricks.SetVariableBrick(formula, var_obj('q'))

        formula = catrobat.create_formula_for(
            [catformula.Operators.MULT,
                var_id('v'),
                ["()", [catformula.Operators.MINUS,
                        1,
                        [catformula.Operators.MULT,
                         var_id('s'), ["()", [catformula.Operators.MINUS, 1, var_id('f')]]]]]])
        set_t_brick = catbricks.SetVariableBrick(formula, var_obj('t'))

        formula = catrobat.create_formula_for(
                [catformula.Operators.LOGICAL_OR,
                 [catformula.Operators.EQUAL, var_id('h_i'), 0],
                 [catformula.Operators.EQUAL, var_id('h_i'), 6]])
        if_h_i_0_or_6_brick = catbricks.IfThenLogicBeginBrick(formula)

        if_h_i_is_value_bricks = {}
        for i in range(1, 6):
            formula = catrobat.create_formula_for([catformula.Operators.EQUAL, var_id('h_i'), i])
            if_h_i_is_value_bricks[i] = catbricks.IfThenLogicBeginBrick(formula)

        def add_set_rgb_variable_bricks_to_if_brick(if_brick, r, g, b):
            for (color, name) in [(r, 'r'), (g, 'g'), (b, 'b')]:
                variable_id = var_id(color)
                formula = catrobat.create_formula_for(
                    [catformula.Functions.ROUND, [catformula.Operators.MULT, variable_id, 255]]
                )
                set_brick = catbricks.SetVariableBrick(formula, var_obj(name))
                if_brick.ifBranchBricks.add(set_brick)
            return

        add_set_rgb_variable_bricks_to_if_brick(if_h_i_0_or_6_brick, 'v', 't', 'p')
        add_set_rgb_variable_bricks_to_if_brick(if_h_i_is_value_bricks[1], 'q', 'v', 'p')
        add_set_rgb_variable_bricks_to_if_brick(if_h_i_is_value_bricks[2], 'p', 'v', 't')
        add_set_rgb_variable_bricks_to_if_brick(if_h_i_is_value_bricks[3], 'p', 'q', 'v')
        add_set_rgb_variable_bricks_to_if_brick(if_h_i_is_value_bricks[4], 't', 'p', 'v')
        add_set_rgb_variable_bricks_to_if_brick(if_h_i_is_value_bricks[5], 'v', 'p', 'q')

        set_pen_color_brick = catbricks.SetPenColorBrick(
            catrobat.create_formula_for(var_id('r')),
            catrobat.create_formula_for(var_id('g')),
            catrobat.create_formula_for(var_id('b'))
        )

        return [set_h_i_brick, set_f_brick, set_p_brick, set_q_brick, set_t_brick, if_h_i_0_or_6_brick] + \
            if_h_i_is_value_bricks.values() + [set_pen_color_brick]

    def get_hsv_pen_color_variables(self):
        return (self.sprite.getUserVariable(scratch.S2CC_PEN_COLOR_VARIABLE_NAMES[variable_name]) for
                variable_name in ['h', 's', 'v'])

    @_register_handler(_block_name_to_handler_map, "penColor:")
    def _convert_pen_color_block(self):
        [argument_color] = self.arguments

        (h_variable, s_variable, v_variable) = self.get_hsv_pen_color_variables()

        is_add_color_variable_bricks = False
        if (isinstance(h_variable, catformula.UserVariable) and isinstance(s_variable, catformula.UserVariable)
            and isinstance(v_variable, catformula.UserVariable)):
            is_add_color_variable_bricks = True

        def add_color_variable_bricks(h, s, v):
            h_formula = catrobat.create_formula_for(h)
            s_formula = catrobat.create_formula_for(s)
            v_formula = catrobat.create_formula_for(v)

            set_h_variable_brick = catbricks.SetVariableBrick(h_formula, h_variable)
            set_s_variable_brick = catbricks.SetVariableBrick(s_formula, s_variable)
            set_v_variable_brick = catbricks.SetVariableBrick(v_formula, v_variable)

            return [set_h_variable_brick, set_s_variable_brick, set_v_variable_brick]

        def convert_rgb_to_hsv(r, g, b):
            return colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

        if isinstance(argument_color, basestring):
            colors_hex = argument_color[1:]
            (r, g, b) = tuple(int(colors_hex[i:i+2], 16) for i in (0, 2, 4))

            if not is_add_color_variable_bricks:
                return catbricks.SetPenColorBrick(r, g, b)

            (h, s, v) = convert_rgb_to_hsv(r, g, b)
            pen_color_variable_bricks = add_color_variable_bricks(h, s, v)
            hsv_to_rgb_bricks = self._add_hsv_to_rgb_conversion_algorithm_bricks()

            return pen_color_variable_bricks + hsv_to_rgb_bricks

        elif isinstance(argument_color, catformula.FormulaElement):
            # formula in a change color brick only affects the blue value in RGB, and the value in HSV respectively

            if not is_add_color_variable_bricks:
                r = catrobat.create_formula_for(0)
                g = catrobat.create_formula_for(0)
                b = catrobat.create_formula_for([catformula.Functions.MOD, ["()", argument_color], 256])
                return catbricks.SetPenColorBrick(r, g, b)

            h = 0.66
            s = 1.0

            # 0 <= ( arg % 256 / 255 ) <= 1
            v = catrobat.create_formula_element_for(
                [catformula.Operators.DIVIDE, [catformula.Functions.MOD, ["()", argument_color], 256], 255.0])

            pen_color_variable_bricks = add_color_variable_bricks(h, s, v)
            hsv_to_rgb_bricks = self._add_hsv_to_rgb_conversion_algorithm_bricks()

            return pen_color_variable_bricks + hsv_to_rgb_bricks

        return catbricks.NoteBrick("Change pen color brick: Unsupported Argument Type")

    @_register_handler(_block_name_to_handler_map, "setPenParamTo:")
    def _convert_set_pen_color_param_block(self):
        [colorparam, value] = self.arguments

        if colorparam == "transparency":
            log.warn("Returning Note Brick for 'setPenParamTo:'. Reason: colorparam = 'transparency'")
            return catbricks.NoteBrick("Sorry, we currently do not support transparency changes!")
        assert colorparam in ["color", "saturation", "brightness"]

        (h_variable, s_variable, v_variable) = self.get_hsv_pen_color_variables()
        assert(isinstance(h_variable, catformula.UserVariable) and isinstance(s_variable, catformula.UserVariable)
               and isinstance(v_variable, catformula.UserVariable))

        if colorparam == "color":
            formula = catrobat.create_formula_for(
                [catformula.Functions.MOD, [catformula.Operators.DIVIDE, ["()", value], 100], 1])
        else:
            formula = catrobat.create_formula_for(
                [catformula.Functions.MAX,
                    [catformula.Functions.MIN,
                     [catformula.Operators.DIVIDE, ["()", value], 100],
                     1],
                    0])

        param_variable_mapping = {"color": h_variable, "saturation": s_variable, "brightness": v_variable}
        set_variable_brick = catbricks.SetVariableBrick(formula, param_variable_mapping[colorparam])

        return [set_variable_brick] + self._add_hsv_to_rgb_conversion_algorithm_bricks()

    @_register_handler(_block_name_to_handler_map, "changePenParamBy:")
    def _convert_change_pen_color_block(self):
        [colorparam, value] = self.arguments

        if (colorparam == "transparency"):
            log.warn("Returning Note Brick for 'changePenParamBy:'. Reason: colorparam = 'transparancy'")
            return catbricks.NoteBrick("Sorry, we currently do not support transparancy changes!")
        assert colorparam in ["color", "saturation", "brightness"]

        (h_variable, s_variable, v_variable) = self.get_hsv_pen_color_variables()
        assert(isinstance(h_variable, catformula.UserVariable) and isinstance(s_variable, catformula.UserVariable)
               and isinstance(v_variable, catformula.UserVariable))

        param_name_mapping = {"color": "h", "saturation": "s", "brightness": "v"}
        var_id = catrobat.build_var_id(scratch.S2CC_PEN_COLOR_VARIABLE_NAMES[param_name_mapping[colorparam]])
        if colorparam == "color":
            formula = catrobat.create_formula_for(
                [catformula.Functions.MOD,
                    [catformula.Operators.PLUS, var_id, [catformula.Operators.DIVIDE, ["()", value], 100]],
                    1])
        else:
            formula = catrobat.create_formula_for(
                [catformula.Functions.MAX,
                 [catformula.Functions.MIN,
                  [catformula.Operators.PLUS, var_id, [catformula.Operators.DIVIDE, ["()", value], 100]],
                  1],
                 0])

        param_variable_mapping = {"color": h_variable, "saturation": s_variable, "brightness": v_variable}
        set_variable_brick = catbricks.SetVariableBrick(formula, param_variable_mapping[colorparam])

        return [set_variable_brick] + self._add_hsv_to_rgb_conversion_algorithm_bricks()

    # Scratch' pen size is ~3.65x (scratch.S2CC_PEN_SIZE_MULTIPLIER) bigger than Catrobat's
    @staticmethod
    def build_pen_size_formula(value):
        return catformula.Formula(catrobat.create_formula_element_for(
            [catformula.Operators.MULT, ["()", value], scratch.S2CC_PEN_SIZE_MULTIPLIER]))

    @_register_handler(_block_name_to_handler_map, "penSize:")
    def _convert_pen_size_block(self):
        [new_pen_size] = self.arguments
        pen_size_variable = self.sprite.getUserVariable(scratch.S2CC_PEN_SIZE_VARIABLE_NAME)

        new_pen_size_formula = self.build_pen_size_formula(new_pen_size)

        if not isinstance(pen_size_variable, catformula.UserVariable):
            return catbricks.SetPenSizeBrick(new_pen_size_formula)

        set_pen_size_variable_brick = catbricks.SetVariableBrick(new_pen_size_formula, pen_size_variable)

        read_pen_size_variable_formula_element = catformula.FormulaElement(
            catElementType.USER_VARIABLE, pen_size_variable.getName(), None
        )
        read_pen_size_variable_formula = catformula.Formula(read_pen_size_variable_formula_element)
        set_pen_size_brick = catbricks.SetPenSizeBrick(read_pen_size_variable_formula)
        return [set_pen_size_variable_brick, set_pen_size_brick]

    @_register_handler(_block_name_to_handler_map, "changePenSizeBy:")
    def _convert_change_pen_size_block(self):
        [change_offset] = self.arguments

        pen_size_variable = self.sprite.getUserVariable(scratch.S2CC_PEN_SIZE_VARIABLE_NAME)
        assert isinstance(pen_size_variable, catformula.UserVariable)

        change_offset_formula = self.build_pen_size_formula(change_offset)
        change_pen_size_variable_brick = catbricks.ChangeVariableBrick(change_offset_formula, pen_size_variable)

        read_pen_size_variable_formula_element = catformula.FormulaElement(
            catElementType.USER_VARIABLE, pen_size_variable.getName(), None
        )
        read_pen_size_variable_formula = catformula.Formula(read_pen_size_variable_formula_element)
        set_pen_size_brick = catbricks.SetPenSizeBrick(read_pen_size_variable_formula)

        return [change_pen_size_variable_brick, set_pen_size_brick]

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

    @_register_handler(_block_name_to_handler_map, "pointTowards:")
    def _convert_point_towards_block(self):
        [sprite_name] = self.arguments

        if not isinstance(sprite_name, basestring):
            return catbricks.NoteBrick("Error: Not a valid parameter for PointToBrick")

        for sprite in self.scene.spriteList:
            if sprite.getName() == sprite_name:
                return self.CatrobatClass(sprite)
        if sprite_name in self.script_context.sprite_context.context.upcoming_sprites:
            sprite = self.script_context.sprite_context.context.upcoming_sprites[sprite_name]
        else:
            sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, sprite_name)
            self.script_context.sprite_context.context.upcoming_sprites[sprite_name] = sprite
        return self.CatrobatClass(sprite)

    @_register_handler(_block_name_to_handler_map, "gotoSpriteOrMouse:")
    def _convert_go_to_sprite_or_mouse_block(self):
        [base_sprite], go_to_brick = self.arguments, None
        if base_sprite == "_random_":
            x_root = catformula.FormulaElement(catElementType.FUNCTION, str(catformula.Functions.RAND), None)
            x_left = catrobat.create_formula_element_with_value(- scratch.STAGE_WIDTH_IN_PIXELS / 2)
            x_right = catrobat.create_formula_element_with_value(scratch.STAGE_WIDTH_IN_PIXELS / 2)
            x_root.setLeftChild(x_left)
            x_root.setRightChild(x_right)
            x_formula = catformula.Formula(x_root)

            y_root = catformula.FormulaElement(catElementType.FUNCTION, str(catformula.Functions.RAND), None)
            y_left = catrobat.create_formula_element_with_value(- scratch.STAGE_HEIGHT_IN_PIXELS / 2)
            y_right = catrobat.create_formula_element_with_value(scratch.STAGE_HEIGHT_IN_PIXELS / 2)
            y_root.setLeftChild(y_left)
            y_root.setRightChild(y_right)
            y_formula = catformula.Formula(y_root)

            go_to_brick = catbricks.PlaceAtBrick(x_formula, y_formula)
        elif isinstance(base_sprite, basestring):
            for sprite in self.scene.spriteList:
                if sprite.getName() == base_sprite:
                    go_to_brick = self.CatrobatClass(sprite)
                    go_to_brick.spinnerSelection = catcommon.BrickValues.GO_TO_OTHER_SPRITE_POSITION
                    return go_to_brick
            if base_sprite in self.script_context.sprite_context.context.upcoming_sprites:
                new_sprite = self.script_context.sprite_context.context.upcoming_sprites[base_sprite]
            else:
                new_sprite = SpriteFactory().newInstance(SpriteFactory.SPRITE_SINGLE, base_sprite)
                self.script_context.sprite_context.context.upcoming_sprites[new_sprite.getName()] = new_sprite

            go_to_brick = self.CatrobatClass(new_sprite)
            go_to_brick.spinnerSelection = catcommon.BrickValues.GO_TO_OTHER_SPRITE_POSITION
        else:
            return catbricks.NoteBrick("Error: Not a valid parameter for Goto Brick")
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

    @_register_handler(_block_name_to_handler_map, "broadcast:")
    def _convert_broadcast(self):
        message = self.arguments[0]
        if isinstance(message, catformula.FormulaElement):
            log.error("Replacing {0} with NoteBrick".format(self.block_name))
            return catbricks.NoteBrick("Catroid doesn't support formula elements for broadcasting")
        elif isinstance(message ,int):
            message = str(message)
        return catbricks.BroadcastBrick(message.lower())

    @_register_handler(_block_name_to_handler_map, "doBroadcastAndWait")
    def _convert_doBroadcastAndWait(self):
        message = self.arguments[0]
        if isinstance(message, catformula.FormulaElement):
            log.error("Replacing {0} with NoteBrick".format(self.block_name))
            return catbricks.NoteBrick("Catroid doesn't support formula elements for broadcasting")
        elif isinstance(message ,int):
            message = str(message)
        return catbricks.BroadcastWaitBrick(message.lower())

    #Note: NoteBricks are not implemented in scratch. We insert one in the Scratch3 parser if there is a problem(e.g.
    # a block that is not implemented in Catroid) when parsing a block.
    @_register_handler(_block_name_to_handler_map, "note:")
    def _convert_note_block(self):
        arg = self.arguments[0]
        if isinstance(arg, (str, unicode)) or isinstance(arg, catformula.Formula):
            return self.CatrobatClass(arg)
        log.warn("Invalid argument for NoteBrick: " + arg)
