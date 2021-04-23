import json
import unittest
import sys
import os
from scratchtocatrobat.scratch.scratch3 import is_scratch3_project
from scratchtocatrobat.scratch.scratch3visitor.looks import *
from scratchtocatrobat.scratch.scratch3 import Scratch3Block
from scratchtocatrobat.scratch.scratch3 import Scratch3Parser
from scratchtocatrobat.scratch.scratch3visitor.visitorUtil import BlockContext, visitBlock, visitLiteral

from scratchtocatrobat.scratch.scratch3visitor.scratch2_json_format import AppliedBlockNumbers
# Those are common input/field/menu types in scratch.
from scratchtocatrobat.scratch.scratch3visitor.scratch2_json_format import MenuTypes, InputTypes, ProcedureTypes, Modifier, Defaults, FieldTypes
# Here is the mapping from scratch 3 to scratch 2 opcodes done
from scratchtocatrobat.scratch.scratch3visitor.scratch2_json_format import Scratch3_2Opcodes as opcodes


# define more enums here, if necessary
class InputType(object):
    LITERAL = 1
    BLOCK_NO_SHADOW = 2
    BLOCK = 3
    PROCEDURE = 4


class LiteralType(object):
    INT = 1
    STRING = 2
    SHADOW_BLOCK = 3
    NON_SHADOW_BLOCK = 4
    SHADOW_STRING = 5
    NON_SHADOW_STRING = 6


class AbstractInput(object):
    KEY_SPACE = "key_space"
    TEST_LOOK = "look1"
    TEST_STRING = "teststring"
    TEST_SOUND = "test_sound"
    SENSOR_LOUDNESS = "loudness"
    MOTION_RANDOM = "_random_"
    DISTANCE_TO_RANDOM = "dist_random"
    NUMBERNAME_NAME = "name"
    NUMBERNAME_NUMBER = "number"
    TEST_CLONE = "_myself_"
    PARAM = "a"
    YEAR = 'year'
    MOUSE = "_mouse_"
    DIRECTION = "direction"
    OBJECT = "_stage_"
    COLOR = "color"


class AbstractType(object):
    BLOCK = 1
    KEY_PRESSED = 2
    LOOK = 3
    BROADCAST_MESSAGE = 4
    SENSOR = 5
    MOTION = 6
    DISTANCE = 7
    NUMBERNAME_NUMBER = 8
    NUMBERNAME_NAME = 9
    SOUND = 10
    CLONE = 11
    PARAM = 12
    YEAR = 13
    MOUSE = 14
    DIRECTION = 15
    OBJECT = 16
    COLOR = 17

    input = {BLOCK: "", KEY_PRESSED: AbstractInput.KEY_SPACE, LOOK: AbstractInput.TEST_LOOK,
             BROADCAST_MESSAGE: AbstractInput.TEST_STRING, SENSOR: AbstractInput.SENSOR_LOUDNESS,
             MOTION: AbstractInput.MOTION_RANDOM, DISTANCE: AbstractInput.DISTANCE_TO_RANDOM,
             NUMBERNAME_NAME: AbstractInput.NUMBERNAME_NAME, NUMBERNAME_NUMBER: AbstractInput.NUMBERNAME_NUMBER,
             SOUND: AbstractInput.TEST_SOUND, CLONE: AbstractInput.TEST_CLONE, PARAM: AbstractInput.PARAM, YEAR: AbstractInput.YEAR,
             MOUSE: AbstractInput.MOUSE, DIRECTION: AbstractInput.DIRECTION, OBJECT: AbstractInput.OBJECT,
             COLOR: AbstractInput.COLOR
             }


class Types(object):
    TEST_MOTION = "test_motion"
    TEST_SOUND = "test_sound"
    TEST_STRING = "teststring"
    TEST_INT = 1234.0



def addInputToBlock(block, key, value, input_type):
    if input_type == InputType.LITERAL:
        block.inputs[key] = [input_type, [4, value]]
    elif input_type == InputType.BLOCK_NO_SHADOW:
        block.inputs[key] = [input_type, value]  # currently, only this case occurs in the tests
    else:
        block.inputs[key] = [input_type, value, [2, "shadow_value"]]


prebuilt_input_types = {LiteralType.STRING: [1, [AppliedBlockNumbers.String, Types.TEST_STRING]],
                        LiteralType.INT: [1, [AppliedBlockNumbers.Number, 1234]],
                        LiteralType.SHADOW_BLOCK: [1, "PLACEHOLDER"],
                        LiteralType.NON_SHADOW_BLOCK: [2, "PLACEHOLDER"],
                        LiteralType.NON_SHADOW_STRING: [3, "PLACEHOLDER", [AppliedBlockNumbers.String, Types.TEST_STRING]]
                        }

# adds input using the prebuilt input types above
#  if menu_name is not None only  and literaltype do not match
def addInputOfType(block, key, literal_type, menu_name = None):
    if (menu_name is None and literal_type != LiteralType.STRING and literal_type != LiteralType.INT) or\
        (menu_name is not None and (literal_type == LiteralType.STRING or literal_type == LiteralType.INT)):
        assert False and "Invalid menu name and literal combination"


    if literal_type in prebuilt_input_types:
        value = list(prebuilt_input_types[literal_type])
        if menu_name is not None:
            value[1] = menu_name
    else:
        return
    block.inputs[key] = value

# adds a Field with the given AbstracType to the given block
def addFieldOfType(block, key, input_type):
    if input_type in AbstractType.input:
        value = [AbstractType.input[input_type]]
    else:
        return
    block.fields[key] = value

# adds a menu block to the context passed
def add_menu_block(context, opcode, menu_name, value):
    menu_block = add_new_block_to_context(context, opcode)
    menu_block.fields[menu_name] = [value]
    context.block.inputs[menu_name] = [1, menu_block.name]
    return menu_block


def create_block_context(opcode):
    context = BlockContext(None, {})
    block = createScratch3Block(context, opcode)
    context.block = block

    context.spriteblocks[block.name] = block
    return context


def generate_proccode(modifier):
    proccode = ProcedureTypes.DEFAULT_PROCCODE
    for mod in modifier:
        proccode += " {m} ".format(m=mod)
    proccode = proccode[:-1]
    return proccode


def userdefined_bricks_generate_arg_names_and_defaults(argument_names, argument_defaults):
    arg_names = "["
    arg_defaults = "["
    for arg in range(len(argument_names)):
        arg_names += "\"{m}\",".format(m=argument_names[arg])
        arg_defaults += "\"{m}\",".format(m=argument_defaults[arg])
        if arg == len(argument_names)-1:
            arg_names = arg_names[:-1]
            arg_defaults = arg_defaults[:-1]
    arg_names += "]"
    arg_defaults += "]"
    return arg_names, arg_defaults


def userdefined_bricks_generate_arguments(mutations_to_add, add_input_type=False, block=None):
    argumentids = "["
    for i in range(mutations_to_add):
        if add_input_type:
            addInputOfType(block,"{m} {n}".format(m=InputTypes.MUTATION, n=i) , LiteralType.STRING)
        argumentids += "\"{m} {n}\",".format(m=InputTypes.MUTATION, n=i)
        if i == mutations_to_add-1:
            argumentids = argumentids[:-1]
            argumentids += "]"
    return argumentids


def add_mutation(block, prototype, modifier, mutations_to_add, argument_names=None, argument_defaults=None):
    if argument_names is None:
        argument_names = []
    if argument_defaults is None:
        argument_defaults = []

    if prototype:
        assert(mutations_to_add == len(argument_names) == len(argument_defaults) == len(modifier))
    else:
        assert(mutations_to_add == len(modifier))

    argumentids = userdefined_bricks_generate_arguments(mutations_to_add, True, block)

    proccode = generate_proccode(modifier)
    block.mutation ={
        "tagName": ProcedureTypes.MUTATION,
        "children": [],
        "proccode": proccode,
        "argumentids": argumentids,
        "warp" : "false",
    }

    arg_names, arg_defaults = userdefined_bricks_generate_arg_names_and_defaults(argument_names, argument_defaults)

    if prototype:
        block.mutation['argumentnames'] = arg_names
        block.mutation['argumentdefaults'] = arg_defaults

# creates a userdefined brick containing a brick of type "inner_opcode", used for testing every block with user defined
# bricks
def create_user_defined_brick(inner_opcode, modifier, default_value, inner_key, shadow_literal):
    context = create_block_context(opcodes.CONTROL_PROCEDURES_DEFINITION)
    definition_block = context.block
    prototype_block = add_new_block_to_context(context, opcodes.CONTROL_PROCEDURES_PROTOTYPE)
    inner_block = add_new_block_to_context(context, inner_opcode)
    arg_rep_bool1 = add_new_block_to_context(context, opcodes.CONTROL_ARGUMENT_REPORTER_BOOL)
    arg_rep_bool2 = add_new_block_to_context(context, opcodes.CONTROL_ARGUMENT_REPORTER_BOOL)

    definition_block.nextBlock = inner_block
    addInputOfType(definition_block, ProcedureTypes.DEFINTION, LiteralType.SHADOW_BLOCK, prototype_block.name)

    addInputOfType(prototype_block, "{m} {n}".format(m=InputTypes.MUTATION, n=0), LiteralType.SHADOW_BLOCK, arg_rep_bool1.name)

    arg_rep_bool1.parentBlock = prototype_block
    addFieldOfType(arg_rep_bool1, MenuTypes.PARAM_VALUE, AbstractType.PARAM)
    add_mutation(prototype_block, True, [modifier], 1, [AbstractInput.PARAM], [default_value])

    prototype_block.parentBlock = definition_block
    inner_block.parentBlock = definition_block

    addInputOfType(inner_block, inner_key, shadow_literal, arg_rep_bool2.name)

    arg_rep_bool2.parentBlock = inner_block
    addFieldOfType(arg_rep_bool2, MenuTypes.PARAM_VALUE, AbstractType.PARAM)
    return context



def createScratch3Block(context, opcode):
    name = opcode + "_" + str(len(context.spriteblocks))
    block = {}
    block['name'] = name

    block['opcode'] = opcode
    block['inputs'] = {}
    block['fields'] = {}
    block["parent"] = None
    block["next"] = None
    block = Scratch3Block(block, name)
    context.spriteblocks[name] = block

    return block


def add_new_block_to_context(context, opcode):
    block = createScratch3Block(context, opcode)
    context.spriteblocks[block.name] = block
    return block


def create_dummy_formula_block(context):
    operator = createScratch3Block(context, "operator_add")
    addInputOfType(operator, "NUM1", LiteralType.INT)
    addInputOfType(operator, "NUM2", LiteralType.INT)
    context.spriteblocks[operator.name] = operator
    return [InputType.BLOCK_NO_SHADOW, operator.name]


class TestScratch3Blocks(unittest.TestCase):
    def setUp(self):
        pass

    ### testcases for event.py ###################
    def test_visitWhenflagclicked(self):
        context = create_block_context(opcodes.FLAG_CLICKED)
        converted_block = visitBlock(context)
        assert len(converted_block) == 1
        assert converted_block[0] == opcodes.opcode_map[opcodes.FLAG_CLICKED]

    def test_visitBroadcast(self):
        context = create_block_context(opcodes.BROADCAST)
        testblock = context.block
        addInputOfType(testblock, InputTypes.BROADCAST_INPUT, LiteralType.STRING)
        converted_block = visitBlock(context)
        assert len(converted_block) == 2
        assert converted_block[0] == opcodes.opcode_map[opcodes.BROADCAST]
        assert converted_block[1] == AbstractInput.TEST_STRING

    def test_visitBroadcastandwait(self):
        context = create_block_context(opcodes.BROADCAST_AND_WAIT)
        testblock = context.block
        addInputOfType(testblock, InputTypes.BROADCAST_INPUT, LiteralType.STRING)
        converted_block = visitBlock(context)
        assert len(converted_block) == 2
        assert converted_block[0] == opcodes.opcode_map[opcodes.BROADCAST_AND_WAIT]
        assert converted_block[1] == AbstractInput.TEST_STRING

    def test_visitWhenthisspriteclicked(self):
        context = create_block_context(opcodes.SPRITE_CLICKED)
        converted_block = visitBlock(context)
        assert len(converted_block) == 1
        assert converted_block[0] == opcodes.opcode_map[opcodes.SPRITE_CLICKED]

    def test_visitWhenkeypressed(self):
        context = create_block_context(opcodes.KEY_PRESSED)
        testblock = context.block
        addFieldOfType(testblock, FieldTypes.KEY_OPTION, AbstractType.KEY_PRESSED)
        converted_block = visitBlock(context)
        assert len(converted_block) == 2
        assert converted_block[0] == opcodes.opcode_map[opcodes.KEY_PRESSED]
        assert converted_block[1] == AbstractInput.KEY_SPACE

    def test_visitWhenbackdropswitchesto(self):
        context = create_block_context(opcodes.BACKDROP_SWITCHED_TO)
        testblock = context.block
        addFieldOfType(testblock, FieldTypes.BACKDROP, AbstractType.LOOK)
        converted_block = visitBlock(context)
        assert len(converted_block) == 2
        assert converted_block[0] == opcodes.opcode_map[opcodes.BACKDROP_SWITCHED_TO]
        assert converted_block[1] == AbstractInput.TEST_LOOK

    def test_visitWhenbroadcastreceived(self):
        context = create_block_context(opcodes.BROADCAST_RECEIVED)
        testblock = context.block
        addFieldOfType(testblock, FieldTypes.BROADCAST_OPTION, AbstractType.BROADCAST_MESSAGE)
        converted_block = visitBlock(context)
        assert len(converted_block) == 2
        assert converted_block[0] == opcodes.opcode_map[opcodes.BROADCAST_RECEIVED]
        assert converted_block[1] == AbstractInput.TEST_STRING

    def test_visitWhengreaterthan(self):
        context = create_block_context(opcodes.GREATER_THAN)
        testblock = context.block
        addFieldOfType(testblock, FieldTypes.WHEN_GREATER_THAN_MENU, AbstractType.SENSOR)
        addInputOfType(testblock, InputTypes.VALUE, LiteralType.INT)
        converted_block = visitBlock(context)
        assert len(converted_block) == 3
        assert converted_block[0] == opcodes.opcode_map[opcodes.GREATER_THAN]
        assert converted_block[1] == AbstractInput.SENSOR_LOUDNESS
        assert converted_block[2] == 1234

    ### Look block testcases ###################
    def test_showSpriteBlock(self):
        context = create_block_context(opcodes.LOOKS_SHOW)
        testblock = context.block
        addInputToBlock(testblock,"myval", 1, InputType.BLOCK_NO_SHADOW)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_SHOW]

        context = create_block_context(opcodes.LOOKS_SHOW)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_SHOW]

    def test_visitGoforwardbackwardlayers(self):
        context = create_block_context(opcodes.LOOKS_FORWARD_BACKWARD_LAYERS)
        testblock = context.block
        testblock.fields["FORWARD_BACKWARD"] = ["forward"]
        addInputOfType(testblock, "NUM", LiteralType.INT)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_FORWARD_BACKWARD_LAYERS]

    def test_visitGoforwardbackwardlayers_formula(self):
        context = create_block_context(opcodes.LOOKS_FORWARD_BACKWARD_LAYERS)
        testblock = context.block
        testblock.fields["FORWARD_BACKWARD"] = ["forward"]
        formula = create_dummy_formula_block(context)
        testblock.inputs["NUM"] = formula
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_FORWARD_BACKWARD_LAYERS]
        assert len(converted_block[1]) == 3
        assert converted_block[1][0] == "+"

    def test_visitSayforsecs(self):
        context = create_block_context(opcodes.LOOKS_SAY_FOR_SECS)
        testblock = context.block
        addInputOfType(testblock, "SECS", LiteralType.INT)
        addInputOfType(testblock, "MESSAGE", LiteralType.STRING)

        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_SAY_FOR_SECS]
        assert converted_block[1] == "teststring"
        assert converted_block[2] == 1234.0


    def test_visitSay(self):
        context = create_block_context(opcodes.LOOKS_SAY)
        testblock = context.block
        addInputOfType(testblock, InputTypes.MESSAGE, LiteralType.STRING)

        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_SAY]
        assert converted_block[1] == Types.TEST_STRING


        context = create_user_defined_brick(opcodes.LOOKS_SAY, Modifier.STRING_OR_NUMBER, Defaults.PARAM_STRING,InputTypes.MESSAGE, LiteralType.NON_SHADOW_STRING)
        converted_block = visitBlock(context)

        assert converted_block[1][0] == opcodes.opcode_map[opcodes.LOOKS_SAY]
        assert len(converted_block[1][1]) == 3
        assert converted_block[1][1][0] == opcodes.opcode_map[opcodes.CONTROL_ARGUMENT_REPORTER_STRING]
        assert converted_block[1][1][1] == AbstractInput.PARAM
        assert converted_block[1][1][2] == Defaults.REPORTER

    def test_visitThinkforsecs(self):
        context = create_block_context(opcodes.LOOKS_THINK_FOR_SECS)
        testblock = context.block
        addInputOfType(testblock, "MESSAGE", LiteralType.STRING)
        addInputOfType(testblock, "SECS", LiteralType.INT)

        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_THINK_FOR_SECS]
        assert converted_block[1] == "teststring"
        assert converted_block[2] == 1234.0

    def test_visitThink(self):
        context = create_block_context(opcodes.LOOKS_THINK)
        testblock = context.block
        addInputOfType(testblock, "MESSAGE", LiteralType.STRING)

        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_THINK]
        assert converted_block[1] == "teststring"

    def test_visitSwitchCostumeTo(self):
        context = create_block_context(opcodes.LOOKS_SWITCH_COSTUME_TO)
        testblock = context.block
        addInputOfType(testblock, "COSTUME", LiteralType.STRING)

        block2 = add_new_block_to_context(context, "looks_costume")
        block2.fields["COSTUME"] = ["test_costume"]
        testblock.inputs["COSTUME"] = [1, block2.name]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_SWITCH_COSTUME_TO]
        assert converted_block[1] == "test_costume"

    def test_visitNextCostume(self):
        context = create_block_context(opcodes.LOOKS_NEXT_COSTUME)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_NEXT_COSTUME]

    def test_visitSwitchBackdropTo(self):
        context = create_block_context(opcodes.LOOKS_SWITCH_BACKDROP_TO)
        testblock = context.block
        addInputOfType(testblock, "BACKDROP", LiteralType.STRING)

        block2 = add_new_block_to_context(context, "looks_backdrops")
        block2.fields["BACKDROP"] = ["test_costume"]
        addInputToBlock(testblock, "BACKDROP", block2.name, InputType.BLOCK_NO_SHADOW)
        testblock.inputs["BACKDROP"] = [1, block2.name]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_SWITCH_BACKDROP_TO]
        assert converted_block[1] == "test_costume"

    def test_visitNextBackdrop(self):
        context = create_block_context(opcodes.LOOKS_NEXT_BACKDROP)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_NEXT_BACKDROP]

    def test_visitChangesizeby(self):
        context = create_block_context(opcodes.LOOKS_CHANGE_SIZE_BY)
        testblock = context.block
        addInputOfType(testblock, "CHANGE", LiteralType.INT)

        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_CHANGE_SIZE_BY]
        assert converted_block[1] == 1234.0

    def test_visitSetsizeto(self):
        context = create_block_context(opcodes.LOOKS_SET_SIZE_TO)
        testblock = context.block
        addInputOfType(testblock, "SIZE", LiteralType.INT)

        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_SET_SIZE_TO]
        assert converted_block[1] == 1234.0

    def test_visitChangeeffectby(self):
        context = create_block_context(opcodes.LOOKS_CHANGE_EFFECT_BY)
        testblock = context.block
        addInputOfType(testblock, "CHANGE", LiteralType.INT)
        testblock.fields["EFFECT"] = ["testeffect"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_CHANGE_EFFECT_BY]
        assert converted_block[1] == "testeffect"
        assert converted_block[2] == 1234.0

    def test_visitSeteffectto(self):
        context = create_block_context(opcodes.LOOKS_SET_EFFECT_TO)
        testblock = context.block
        addInputOfType(testblock, "VALUE", LiteralType.INT)
        testblock.fields["EFFECT"] = ["testeffect"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_SET_EFFECT_TO]
        assert converted_block[1] == "testeffect"
        assert converted_block[2] == 1234.0

    def test_visitCleargraphiceffects(self):
        context = create_block_context(opcodes.LOOKS_CLEAR_EFFECTS)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_CLEAR_EFFECTS]

    def test_visitHide(self):
        context = create_block_context(opcodes.LOOKS_HIDE)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_HIDE]

    def test_visitGotofrontback(self):
        context = create_block_context(opcodes.LOOKS_GOTO_FRONT_BACK)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_GOTO_FRONT_BACK]

    def test_visitCostume(self):
        context = create_block_context(opcodes.LOOKS_COSTUME)
        addFieldOfType(context.block, MenuTypes.COSTUME, AbstractType.LOOK)
        converted_block = visitBlock(context)
        assert converted_block[0] == AbstractInput.TEST_LOOK

    def test_visitBackdrop(self):
        context = create_block_context(opcodes.LOOKS_BACKDROPS)
        addFieldOfType(context.block, MenuTypes.BACKDROP, AbstractType.LOOK)
        converted_block = visitBlock(context)
        assert converted_block[0] == AbstractInput.TEST_LOOK

    def test_visitCostumenumbername(self):
        context = create_block_context(opcodes.LOOKS_COSTUME_NUMBER_NAME)
        addFieldOfType(context.block, MenuTypes.NUMBER_NAME, AbstractType.NUMBERNAME_NUMBER)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_COSTUME_NUMBER_NAME + "_number"]

        context = create_block_context(opcodes.LOOKS_COSTUME_NUMBER_NAME)
        addFieldOfType(context.block, MenuTypes.NUMBER_NAME, AbstractType.NUMBERNAME_NAME)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_COSTUME_NUMBER_NAME + "_name"]

    def test_visitSize(self):
        context = create_block_context(opcodes.LOOKS_SIZE)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.LOOKS_SIZE]

    ######### Sound Blocks #########################################

    def test_visitPlay(self):
        context = create_block_context(opcodes.SOUNDS_PLAY)
        add_menu_block(context, opcodes.SOUNDS_MENU, MenuTypes.SOUND_MENU, Types.TEST_SOUND)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.SOUNDS_PLAY]
        assert converted_block[1] == Types.TEST_SOUND

    def test_visitPlayuntildone(self):
        context = create_block_context(opcodes.SOUNDS_PLAY_UNTIL_DONE)
        testblock = context.block
        add_menu_block(context, opcodes.SOUNDS_MENU, MenuTypes.SOUND_MENU, Types.TEST_SOUND)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SOUNDS_PLAY_UNTIL_DONE]
        assert converted_block[1] == Types.TEST_SOUND

    def test_visitStopallsounds(self):
        context = create_block_context(opcodes.SOUNDS_STOP_ALL)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.SOUNDS_STOP_ALL]

    def test_visitClearsoundeffects(self):
        context = create_block_context(opcodes.SOUNDS_CLEAR)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.SOUNDS_CLEAR]

    def test_visitChangeEffectBy_Sound(self):
        # TODO not implemented in Catrobat yet
        # TODO not implemented in Catrobat yet
        pass

    def test_visitSetEffectto_sound(self):
        # TODO not implemented in Catrobat yet
        pass

    def test_visitCleareffects(self):
        # TODO not implemented in scratch2, use workaround
        pass

    def test_visitSounds_menu(self):
        context = create_block_context(opcodes.SOUNDS_MENU)
        addFieldOfType(context.block, MenuTypes.SOUND_MENU, AbstractType.SOUND)
        converted_block = visitBlock(context)
        assert converted_block[0] == AbstractInput.TEST_SOUND

    def test_visitChangevolumeby(self):
        context = create_block_context(opcodes.SOUNDS_CHANGE_VOLUME_BY)
        testblock = context.block
        addInputOfType(testblock, "VOLUME", LiteralType.INT)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.SOUNDS_CHANGE_VOLUME_BY]
        assert converted_block[1] == 1234.0

    def test_visitSetvolumeto(self):
        context = create_block_context(opcodes.SOUNDS_SET_VOLUME_TO)
        testblock = context.block
        addInputOfType(testblock, "VOLUME", LiteralType.INT)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.SOUNDS_SET_VOLUME_TO]
        assert converted_block[1] == 1234.0

    def test_visitVolume(self):
        context = create_block_context(opcodes.SOUNDS_VOLUME)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.SOUNDS_VOLUME]


    ### Sensing objects ##############
    def test_visitTouchingObject(self):
        context = create_block_context(opcodes.SENSING_TOUCHING_OBJECT)
        testblock = context.block
        menublock = createScratch3Block(context, opcodes.SENSING_TOUCHING_OBJECT_MENU)
        addFieldOfType(menublock, MenuTypes.TOUCHING_OBJECT, AbstractType.MOUSE)
        addInputOfType(context.block, MenuTypes.TOUCHING_OBJECT, LiteralType.SHADOW_BLOCK, menublock.name)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_TOUCHING_OBJECT]
        assert converted_block[1] == AbstractInput.MOUSE

    def test_visitTouchingObjectMenu(self):
        context = create_block_context(opcodes.SENSING_TOUCHING_OBJECT_MENU)
        addFieldOfType(context.block, MenuTypes.TOUCHING_OBJECT, AbstractType.MOUSE)
        converted_block = visitBlock(context)
        assert converted_block[0] == AbstractInput.MOUSE

    def test_visitAskandwait(self):
        context = create_block_context(opcodes.SENSING_ASK_AND_WAIT)
        testblock = context.block
        addInputOfType(testblock, "QUESTION", LiteralType.STRING)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_ASK_AND_WAIT]
        assert converted_block[1] == "teststring"

    def test_visitSetdragmode(self):
        context = create_block_context(opcodes.SENSING_SET_DRAG_MODE)
        testblock = context.block
        testblock.fields["DRAG_MODE"] = ["mode"]

        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_SET_DRAG_MODE]
        assert converted_block[1] == "mode"

    def test_visitResettimer(self):
        context = create_block_context(opcodes.SENSING_RESET_TIMER)
        testblock = context.block

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_RESET_TIMER]

    def test_visitLoudness(self):
        context = create_block_context(opcodes.SENSING_LOUDNESS)
        testblock = context.block
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_LOUDNESS]

    def test_visitDistanceto(self):
        context = create_block_context(opcodes.SENSING_DISTANCE_TO)
        testblock = context.block

        menublock = createScratch3Block(context, opcodes.SENSING_TO_DISTANCE_MENU)
        menublock.fields["DISTANCETOMENU"] = ['testsprite']
        testblock.inputs["DISTANCETOMENU"] = [1, menublock.name]

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_DISTANCE_TO]
        assert converted_block[1] == "testsprite"

    def test_visitDistancetomenu(self):
        context = create_block_context(opcodes.SENSING_TO_DISTANCE_MENU)
        addFieldOfType(context.block, MenuTypes.DISTANCE_TO_MENU, AbstractType.DISTANCE)
        converted_block = visitBlock(context)

        assert converted_block[0] == AbstractInput.DISTANCE_TO_RANDOM


    def test_visitColoristouchingcolor(self):
        context = create_block_context(opcodes.SENSING_COLOR_TOUCHING_COLOR)
        testblock = context.block

        addInputOfType(testblock, "COLOR", LiteralType.STRING)
        addInputOfType(testblock, "COLOR2", LiteralType.STRING)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_COLOR_TOUCHING_COLOR]
        assert converted_block[1] == "teststring"
        assert converted_block[2] == "teststring"

    def test_visitCurrent(self):
        context = create_block_context(opcodes.SENSING_CURRENT)

        menublock = createScratch3Block(context, opcodes.SENSING_CURRENT_MENU)
        addFieldOfType(menublock, MenuTypes.CURRENT_MENU, AbstractType.YEAR)
        addInputOfType(context.block, MenuTypes.CURRENT_MENU, LiteralType.SHADOW_BLOCK, menublock.name)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_CURRENT]
        assert converted_block[1] == AbstractInput.YEAR

    def test_visitCurrent_menu(self):
        context = create_block_context(opcodes.SENSING_CURRENT_MENU)
        addFieldOfType(context.block, MenuTypes.CURRENT_MENU, AbstractType.YEAR)
        converted_block = visitBlock(context)
        assert converted_block[0] == AbstractInput.YEAR


    def test_visitAnswer(self):
        context = create_block_context(opcodes.SENSING_ANSWER)
        testblock = context.block

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_ANSWER]

    def test_visitDayssince2000(self):
        context = create_block_context(opcodes.SENSING_DAYS_SINCE_2000)
        testblock = context.block

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_DAYS_SINCE_2000]

    def test_visitKeypressed(self):
        context = create_block_context(opcodes.SENSING_KEYPRESSED)
        testblock = context.block
        menublock = createScratch3Block(context, opcodes.SENSING_KEY_OPTIONS)
        menublock.fields["KEY_OPTION"] = ['a']
        testblock.inputs["KEY_OPTION"] = [1, menublock.name]

        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_KEYPRESSED]
        assert converted_block[1] == "a"

    # def test_visitKey_options(self):
    #     context = create_block_context("sensing_key_options")
    #     testblock = context.block
    #     assert False

    def test_visitMousex(self):
        context = create_block_context(opcodes.SENSING_MOUSEX)
        testblock = context.block

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_MOUSEX]

    def test_visitMousedown(self):
        context = create_block_context(opcodes.SENSING_MOUSE_DOWN)
        testblock = context.block

        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_MOUSE_DOWN]

    def test_visitMousey(self):
        context = create_block_context(opcodes.SENSING_MOUSEY)
        testblock = context.block

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_MOUSEY]

    def test_visitTimer(self):
        context = create_block_context(opcodes.SENSING_TIMER)
        testblock = context.block

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_TIMER]

    def test_visitTouchingcolor(self):
        context = create_block_context(opcodes.SENSING_TOUCHING_COLOR)
        testblock = context.block
        addInputOfType(testblock, "COLOR", LiteralType.STRING)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_TOUCHING_COLOR]
        assert converted_block[1] == "teststring"

    def test_visitUsername(self):
        context = create_block_context(opcodes.SENSING_USERNAME)
        testblock = context.block

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_USERNAME]

    def test_visitOf(self):
        context = create_block_context(opcodes.SENSING_OF)
        testblock = context.block
        addInputOfType(testblock, MenuTypes.OBJECT, LiteralType.STRING)

        addFieldOfType(testblock, FieldTypes.PROPERTY, AbstractType.DIRECTION)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.SENSING_OF]
        assert converted_block[1] == AbstractInput.DIRECTION
        assert converted_block[2] == Types.TEST_STRING

    def test_visitOf_object_menu(self):
        context = create_block_context(opcodes.SENSING_OF_OBJECT_MENU)
        addFieldOfType(context.block, MenuTypes.OBJECT, AbstractType.OBJECT)
        converted_block = visitBlock(context)
        assert converted_block[0] == AbstractInput.OBJECT



    #### Data blocks ###################
    def test_visitSetvarableto(self):
        context = create_block_context(opcodes.DATA_SET_VARIABLE_TO)
        testblock = context.block
        addInputOfType(testblock, "VALUE", LiteralType.INT)
        testblock.fields["VARIABLE"] = ["testvar"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_SET_VARIABLE_TO]
        assert converted_block[1] == "testvar"
        assert converted_block[2] == 1234.0

    def test_visitChangevarableby(self):
        context = create_block_context(opcodes.DATA_CHANGE_VARIABLE_BY)
        testblock = context.block
        addInputOfType(testblock, "VALUE", LiteralType.INT)
        testblock.fields["VARIABLE"] = ["testvar"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_CHANGE_VARIABLE_BY]
        assert converted_block[1] == "testvar"
        assert converted_block[2] == 1234.0

    def test_visitShowVariable(self): #TODO
        context = create_block_context(opcodes.DATA_SHOW_VARIABLE)
        context.block.fields["VARIABLE"] = ["testvar"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_SHOW_VARIABLE]
        assert converted_block[1] == "testvar"

    def test_visitHidevariable(self):
        context = create_block_context(opcodes.DATA_HIDE_VARIABLE)
        testblock = context.block
        testblock.fields["VARIABLE"] = ["testvar"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_HIDE_VARIABLE]
        assert converted_block[1] == "testvar"

    def test_visitAddtolist(self):
        context = create_block_context(opcodes.DATA_ADD_TO_LIST)
        testblock = context.block
        addInputOfType(testblock, "ITEM", LiteralType.INT)
        testblock.fields["LIST"] = ["testlist"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_ADD_TO_LIST]
        assert converted_block[1] == 1234.0
        assert converted_block[2] == "testlist"

    def test_visitDeleteoflist(self):
        context = create_block_context(opcodes.DATA_DELETE_OF_LIST)
        testblock = context.block
        addInputOfType(testblock, "INDEX", LiteralType.INT)
        testblock.fields["LIST"] = ["testlist"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_DELETE_OF_LIST]
        assert converted_block[1] == 1234.0
        assert converted_block[2] == "testlist"

    def test_visitInsertatlist(self):
        context = create_block_context(opcodes.DATA_INSERT_AT_LIST)
        testblock = context.block
        addInputOfType(testblock, "ITEM", LiteralType.INT)
        addInputOfType(testblock, "INDEX", LiteralType.INT)
        testblock.fields["LIST"] = ["testlist"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_INSERT_AT_LIST]
        assert converted_block[1] == 1234.0
        assert converted_block[2] == 1234.0
        assert converted_block[3] == "testlist"

    def test_visitReplaceitemoflist(self):
        context = create_block_context(opcodes.DATA_REPLACE_ITEM_OF_LIST)
        testblock = context.block
        addInputOfType(testblock, "INDEX", LiteralType.INT)
        addInputOfType(testblock, "ITEM", LiteralType.INT)
        testblock.fields["LIST"] = ["testlist"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_REPLACE_ITEM_OF_LIST]
        assert converted_block[1] == 1234.0
        assert converted_block[2] == "testlist"
        assert converted_block[3] == 1234.0

    def test_visitItemoflist(self):
        context = create_block_context(opcodes.DATA_ITEM_OF_LIST)
        testblock = context.block
        addInputOfType(testblock, "INDEX", LiteralType.INT)
        testblock.fields["LIST"] = ["testlist"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_ITEM_OF_LIST]
        assert converted_block[1] == 1234.0
        assert converted_block[2] == "testlist"

    def test_visitItemnumoflist(self):
        context = create_block_context(opcodes.DATA_ITEMNUM_OF_LIST)
        testblock = context.block
        addInputOfType(testblock, "ITEM", LiteralType.INT)
        testblock.fields["LIST"] = ["testlist"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_ITEMNUM_OF_LIST]
        assert converted_block[1] == "testlist"
        assert converted_block[2] == 1234.0

    def test_visitLengthoflist(self):
        context = create_block_context(opcodes.DATA_LENGTH_OF_LIST)
        testblock = context.block
        testblock.fields["LIST"] = ["testlist"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_LENGTH_OF_LIST]
        assert converted_block[1] == "testlist"

    def test_visitListcontainsitem(self):
        context = create_block_context(opcodes.DATA_LIST_CONTAINS_ITEM)
        testblock = context.block
        addInputOfType(testblock, "ITEM", LiteralType.INT)
        testblock.fields["LIST"] = ["testlist"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_LIST_CONTAINS_ITEM]
        assert converted_block[1] == "testlist"
        assert converted_block[2] == 1234.0

    def test_visitShowlist(self):
        context = create_block_context(opcodes.DATA_SHOW_LIST)
        testblock = context.block
        testblock.fields["LIST"] = ["testlist"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_SHOW_LIST]
        assert converted_block[1] == "testlist"

    def test_visitHidelist(self):
        context = create_block_context(opcodes.DATA_HIDE_LIST)
        testblock = context.block
        testblock.fields["LIST"] = ["testlist"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_HIDE_LIST]
        assert converted_block[1] == "testlist"

    def test_visitContentsoflist(self):
        context = create_block_context(opcodes.DATA_CONTENTS_OF_LIST)
        testblock = context.block
        testblock.fields["LIST"] = ["testlist"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.DATA_CONTENTS_OF_LIST]
        assert converted_block[1] == "testlist"

    ### Control blocks ###################
    def test_visitWait(self):
        context = create_block_context(opcodes.CONTROL_WAIT)
        testblock = context.block
        addInputOfType(testblock, "DURATION", LiteralType.INT)
        addInputOfType(testblock, "SUBSTACK", AbstractType.BLOCK)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_WAIT]
        assert converted_block[1] == 1234

    def test_visitRepat(self):
        context = create_block_context(opcodes.CONTROL_REPEAT)
        testblock = context.block
        addInputOfType(testblock, "TIMES", LiteralType.INT)
        testblock.fields["NUMBER_NAME"] = ["name"]


        sayblock = createScratch3Block(context, opcodes.LOOKS_SAY)
        addInputOfType(sayblock, "MESSAGE", LiteralType.STRING)
        testblock.inputs["SUBSTACK"] = [1, sayblock.name]

        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_REPEAT]
        assert converted_block[1] == 1234
        assert converted_block[2][0][0] == opcodes.opcode_map[opcodes.LOOKS_SAY]



    def test_visitIf(self):
        context = create_block_context(opcodes.CONTROL_IF)
        testblock = context.block
        addInputOfType(testblock, "CONDITION", AbstractType.BLOCK)

        sayblock = createScratch3Block(context, opcodes.LOOKS_SAY)
        addInputOfType(sayblock, "MESSAGE", LiteralType.STRING)
        # context.spriteblocks[sayblock.name] = sayblock
        testblock.inputs["CONDITION"] = [1, sayblock.name]
        testblock.inputs["SUBSTACK"] = [1, sayblock.name]

        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_IF]
        assert converted_block[1] == opcodes.opcode_map[opcodes.LOOKS_SAY]
        assert converted_block[2][0][0] == opcodes.opcode_map[opcodes.LOOKS_SAY]
        # test for user defined bricks

        context = create_user_defined_brick(opcodes.CONTROL_IF, Modifier.BOOLEAN, Defaults.PARAM_BOOLEAN, InputTypes.CONDITION,
                                            LiteralType.NON_SHADOW_BLOCK)
        converted_block = visitBlock(context)

        assert converted_block[1][0] == opcodes.opcode_map[opcodes.CONTROL_IF]
        assert len(converted_block[1][1]) == 3
        assert converted_block[1][2] is None
        assert converted_block[1][1][0] == opcodes.opcode_map[opcodes.CONTROL_ARGUMENT_REPORTER_BOOL]
        assert converted_block[1][1][1] == AbstractInput.PARAM
        assert converted_block[1][1][2] == Defaults.REPORTER


    def test_visitIfelse(self):
        context = create_block_context(opcodes.CONTROL_IF_ELSE)
        testblock = context.block
        # addInputOfType(testblock, "CONDITION", TYPE_BLOCK)
        # addInputOfType(testblock, "SUBSTACK1", TYPE_BLOCK)

        sayblock = createScratch3Block(context, opcodes.LOOKS_SAY)
        # context.spriteblocks[sayblock.name] = sayblock
        testblock.inputs["CONDITION"] = [1, sayblock.name]
        testblock.inputs["SUBSTACK"] = [1, sayblock.name]
        testblock.inputs["SUBSTACK2"] = [1, sayblock.name]
        addInputOfType(sayblock, "MESSAGE", LiteralType.STRING)

        # assert converted_block[1][0] in conditionalblocks
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_IF_ELSE]
        assert converted_block[1] == opcodes.opcode_map[opcodes.LOOKS_SAY]
        assert converted_block[2][0][0] == opcodes.opcode_map[opcodes.LOOKS_SAY]
        assert converted_block[3][0][0] == opcodes.opcode_map[opcodes.LOOKS_SAY]


        # assert converted_block[1] == 1234

    def test_visitWait_until(self):
        context = create_block_context(opcodes.CONTROL_WAIT_UNTIL)
        testblock = context.block
        sayblock = createScratch3Block(context, opcodes.LOOKS_SAY)
        addInputOfType(sayblock, "MESSAGE", LiteralType.STRING)
        testblock.inputs["CONDITION"] = [1, sayblock.name]

        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_WAIT_UNTIL]
        assert converted_block[1] == opcodes.opcode_map[opcodes.LOOKS_SAY]

        # assert converted_block[1] == 1234

    def test_visitRepeat_until(self):
        context = create_block_context(opcodes.CONTROL_REPEAT_UNTIL)
        testblock = context.block
        sayblock = createScratch3Block(context, opcodes.LOOKS_SAY)
        addInputOfType(sayblock, "MESSAGE", LiteralType.STRING)

        testblock.inputs["CONDITION"] = [1, sayblock.name]
        testblock.inputs["SUBSTACK"] = [1, sayblock.name]

        # context.spriteblocks[sayblock.name] = sayblock
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_REPEAT_UNTIL]
        assert converted_block[1] == opcodes.opcode_map[opcodes.LOOKS_SAY]
        assert converted_block[2][0][0] == opcodes.opcode_map[opcodes.LOOKS_SAY]

        # assert converted_block[1] == 1234

    def test_visitCreate_clone_of(self):
        context = create_block_context(opcodes.CONTROL_CREATE_CLONE_OF)
        menu_block = add_menu_block(context, opcodes.CONTROL_CREATE_CLONE_OF_MENU, MenuTypes.CLONE_MENU, AbstractInput.TEST_CLONE)
        # addInputOfType(testblock, "CLONE_OPTION", TYPE_BLOCK)
        # addInputToBlock(testblock, "CLONE_OPTION", [1,])
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_CREATE_CLONE_OF]
        assert converted_block[1] == AbstractInput.TEST_CLONE

    def test_visitCreate_clone_of_menu(self):
        context = create_block_context(opcodes.CONTROL_CREATE_CLONE_OF_MENU)
        addFieldOfType(context.block, MenuTypes.CLONE_MENU, AbstractType.CLONE)
        converted_block = visitBlock(context)
        assert converted_block[0] == AbstractInput.TEST_CLONE

    def test_visitStop(self):
        context = create_block_context(opcodes.CONTROL_STOP)
        testblock = context.block
        testblock.fields["STOP_OPTION"] = ["stopthisscript"]
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_STOP]
        assert converted_block[1] == "stopthisscript"


    def test_visitStart_as_clone(self):
        context = create_block_context(opcodes.CONTROL_START_AS_CLONE)
        testblock = context.block
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_START_AS_CLONE]


    def test_visitDelete_this_clone(self):
        context = create_block_context(opcodes.CONTROL_DELETE_THIS_CLONE)
        testblock = context.block
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_DELETE_THIS_CLONE]

    ### testcases for pen.py ###################
    def test_visitClear(self):
        context = create_block_context(opcodes.PEN_CLEAR)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.PEN_CLEAR]

    def test_visitStamp(self):
        context = create_block_context(opcodes.PEN_STAMP)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.PEN_STAMP]

    def test_visitPenDown(self):
        context = create_block_context(opcodes.PEN_DOWN)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.PEN_DOWN]

    def test_visitPenUp(self):
        context = create_block_context(opcodes.PEN_UP)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.PEN_UP]

    def test_visitSetPenColorToColor(self):
        context = create_block_context(opcodes.PEN_SET_COLOR)
        testblock = context.block
        addInputOfType(testblock, InputTypes.COLOR, LiteralType.STRING)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.PEN_SET_COLOR]
        assert converted_block[1] == "teststring"

    def test_visitSetPenColorParamTo(self):
        context = create_block_context(opcodes.PEN_SET_PARAM)
        testblock = context.block
        addInputOfType(testblock, InputTypes.COLOR_PARAM, LiteralType.STRING)
        addInputOfType(testblock, MenuTypes.PARAM_VALUE, LiteralType.INT)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.PEN_SET_PARAM]
        assert converted_block[1] == Types.TEST_STRING
        assert converted_block[2] == 1234

    def test_visitChangePenColorParamBy(self):
        context = create_block_context(opcodes.PEN_CHANGE_COLOR)
        testblock = context.block
        addInputOfType(testblock, InputTypes.COLOR_PARAM, LiteralType.STRING)
        addInputOfType(testblock, MenuTypes.PARAM_VALUE, LiteralType.INT)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.PEN_CHANGE_COLOR]
        assert converted_block[1] == Types.TEST_STRING
        assert converted_block[2] == 1234

    def test_visitPen_menu_colorParam(self):
        context = create_block_context(opcodes.PEN_COLOR_PARAM_MENU)
        addFieldOfType(context.block, MenuTypes.COLOR_PARAM, AbstractType.COLOR)
        converted_block = visitBlock(context)
        assert converted_block[0] == AbstractInput.COLOR


    def test_visitSetPenSizeTo(self):
        context = create_block_context(opcodes.PEN_SET_SIZE)
        testblock = context.block
        addInputOfType(testblock, "SIZE", LiteralType.INT)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.PEN_SET_SIZE]
        assert converted_block[1] == 1234

    def test_visitChangePenSizeBy(self):
        context = create_block_context(opcodes.PEN_CHANGE_SIZE)
        testblock = context.block
        addInputOfType(testblock, "SIZE", LiteralType.INT)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.PEN_CHANGE_SIZE]
        assert converted_block[1] == Types.TEST_INT

    def test_visitSetPenShadeToNumber(self):
        context = create_block_context(opcodes.PEN_SET_SHADE_TO_NUMBER)
        addInputOfType(context.block, InputTypes.SHADE, LiteralType.INT)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.PEN_SET_SHADE_TO_NUMBER]
        assert converted_block[1] == Types.TEST_INT

    def test_visitChangePenShadeByNumber(self):
        context = create_block_context(opcodes.PEN_CHANGE_PEN_SHADE_BY)
        addInputOfType(context.block, InputTypes.SHADE, LiteralType.INT)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.PEN_CHANGE_PEN_SHADE_BY]
        assert converted_block[1] == Types.TEST_INT

    def test_visitSetPenHueToNumber(self):
        context = create_block_context(opcodes.PEN_SET_PEN_HUE_TO_NUMBER)
        addInputOfType(context.block, InputTypes.HUE, LiteralType.INT)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.PEN_SET_PEN_HUE_TO_NUMBER]
        assert converted_block[1] == Types.TEST_INT

    def test_visitForever(self):
        context = create_block_context(opcodes.CONTROL_FOREVER)
        testblock = context.block
        sayblock = createScratch3Block(context, opcodes.LOOKS_SAY)
        context.spriteblocks[sayblock.name] = sayblock
        testblock.inputs["SUBSTACK"] = [1, sayblock.name]
        addInputOfType(sayblock, "MESSAGE", LiteralType.STRING)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_FOREVER]
        assert converted_block[1][0][0] == opcodes.opcode_map[opcodes.LOOKS_SAY]

    def test_visitProcedures_call(self):
        # testing for all of those inputs, just extend the lists if you want to put in more
        # procedure prototype tests
        modifier = [
            ["%b"], ["%s"], ["%b", "%s"], ["%b", "%s"]*3
        ]
        for i in range(len(modifier)):
            context = create_block_context(opcodes.CONTROL_PROCEDURES_CALL)
            mod = modifier[i]
            procedures_call_block = context.block
            add_mutation(procedures_call_block, False, mod, len(mod))
            converted_block = visitBlock(context)
            proccode = generate_proccode(mod)
            assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_PROCEDURES_CALL]
            assert converted_block[1] == proccode
            for i in range(2, len(converted_block)):
                assert converted_block[i] == Types.TEST_STRING

    def test_visitArgument_reporter(self):
        # boolean reporter:
        context = create_block_context(opcodes.CONTROL_ARGUMENT_REPORTER_BOOL)
        addFieldOfType(context.block, MenuTypes.PARAM_VALUE, AbstractType.PARAM)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_ARGUMENT_REPORTER_BOOL]
        assert converted_block[1] == AbstractInput.PARAM
        assert converted_block[2] == "r"

        # string reporter
        context = create_block_context(opcodes.CONTROL_ARGUMENT_REPORTER_STRING)
        addFieldOfType(context.block, MenuTypes.PARAM_VALUE, AbstractType.PARAM)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_ARGUMENT_REPORTER_STRING]
        assert converted_block[1] == AbstractInput.PARAM
        assert converted_block[2] == "r"


    def test_visitProcedures_prototye(self):
        # testing for all of those inputs, just extend the lists if you want to put in more
        # procedure prototype tests
        modifier = [
            [Modifier.BOOLEAN], [Modifier.STRING_OR_NUMBER], [Modifier.BOOLEAN, Modifier.STRING_OR_NUMBER],
            [Modifier.BOOLEAN, Modifier.STRING_OR_NUMBER]*3
        ]
        argument_names = [
            [AbstractInput.PARAM], [AbstractInput.PARAM], ["a", "b"], ["a", "b", "c","d","e","f"]
        ]
        argument_defaults = [
            [Defaults.PARAM_BOOLEAN], [Defaults.PARAM_STRING], ["true", "hi"], [Defaults.PARAM_BOOLEAN, Defaults.PARAM_STRING]*3
        ]
        exppected_names = argument_names
        expected_defaults = [
            [False], [''], [True, "hi"], [False, ""]*3
        ]
        for i in range(len(modifier)):
            context = create_block_context(opcodes.CONTROL_PROCEDURES_PROTOTYPE)
            mod = modifier[i]
            arg_names = argument_names[i]
            arg_defaults = argument_defaults[i]
            procedures_prototype_block = context.block
            add_mutation(procedures_prototype_block, True, mod, len(mod), arg_names, arg_defaults)
            converted_block = visitBlock(context)[0]
            proccode = generate_proccode(mod)
            assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_PROCEDURES_PROTOTYPE]
            assert converted_block[1] == proccode
            assert converted_block[2] == exppected_names[i]
            assert converted_block[3] == expected_defaults[i]
            assert converted_block[4] is False

    def test_Procedures_definition(self):
        modifier = [Modifier.BOOLEAN]
        argument_names = [AbstractInput.PARAM]
        argument_defaults = [Defaults.PARAM_BOOLEAN]
        expected_names = argument_names
        expected_defaults = [False]

        context = create_block_context(opcodes.CONTROL_PROCEDURES_DEFINITION)
        definition_block = context.block
        prototype_block = add_new_block_to_context(context, opcodes.CONTROL_PROCEDURES_PROTOTYPE)

        addInputOfType(definition_block, ProcedureTypes.DEFINTION, LiteralType.SHADOW_BLOCK, prototype_block.name)
        add_mutation(prototype_block, True, modifier, 1, argument_names, argument_defaults)

        proccode = generate_proccode(modifier)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.CONTROL_PROCEDURES_PROTOTYPE]
        assert converted_block[1] == proccode
        assert converted_block[2][0] == expected_names[0]
        assert converted_block[3][0] == expected_defaults[0]
        assert converted_block[4] is Defaults.WARP


    ### Motion block testcases ###################
    def test_visitMovesteps(self):
        context = create_block_context(opcodes.MOTION_MOVE_STEPS)
        testblock = context.block
        addInputOfType(testblock, "STEPS", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_MOVE_STEPS]
        assert converted_block[1] == 1234

    def test_visitTurnright(self):
        context = create_block_context(opcodes.MOTION_TURN_RIGHT)
        testblock = context.block
        addInputOfType(testblock, "DEGREES", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_TURN_RIGHT]
        assert converted_block[1] == 1234

    def test_visitTurnleft(self):
        context = create_block_context(opcodes.MOTION_TURN_LEFT)
        testblock = context.block
        addInputOfType(testblock, "DEGREES", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_TURN_LEFT]
        assert converted_block[1] == 1234

    def test_visitGotoxy(self):
        context = create_block_context(opcodes.MOTION_GOTO_XY)
        testblock = context.block
        addInputOfType(testblock, "X", LiteralType.INT)
        addInputOfType(testblock, "Y", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_GOTO_XY]
        assert converted_block[1] == 1234
        assert converted_block[2] == 1234

    def test_visitGoto(self):
        context = create_block_context(opcodes.MOTION_GOTO)
        testblock = context.block
        addInputOfType(testblock, "TO", LiteralType.STRING)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_GOTO]
        assert converted_block[1] == "teststring"

    def test_visitGlideto(self):
        context = create_block_context(opcodes.MOTION_GLIDE_TO)
        testblock = context.block
        addInputOfType(testblock, "SECS", LiteralType.INT)
        addInputOfType(testblock, "TO", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_GLIDE_TO]
        assert converted_block[1] == 1234

    def test_visitGlidesecstoxy(self):
        context = create_block_context(opcodes.MOTION_GLIDE_SECS_TO_XY)
        testblock = context.block
        addInputOfType(testblock, "SECS", LiteralType.INT)
        addInputOfType(testblock, "X", LiteralType.INT)
        addInputOfType(testblock, "Y", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_GLIDE_SECS_TO_XY]
        assert converted_block[1] == 1234
        assert converted_block[2] == 1234
        assert converted_block[3] == 1234

    def test_visitPointindirection(self):
        context = create_block_context(opcodes.MOTION_POINT_IN_DIR)
        testblock = context.block
        addInputOfType(testblock, "DIRECTION", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_POINT_IN_DIR]
        assert converted_block[1] == 1234

    def test_visitPointtowards(self):
        context = create_block_context(opcodes.MOTION_POINT_TOWARDS)
        testblock = context.block
        addInputOfType(testblock, "TOWARDS", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_POINT_TOWARDS]
        assert converted_block[1] == 1234

    def test_visitChangexby(self):
        context = create_block_context(opcodes.MOTION_CHANGE_BY_XY)
        testblock = context.block
        addInputOfType(testblock, "DX", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_CHANGE_BY_XY]
        assert converted_block[1] == 1234

    def test_visitChangeyby(self):
        context = create_block_context(opcodes.MOTION_CHANGE_Y_BY)
        testblock = context.block
        addInputOfType(testblock, "DY", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_CHANGE_Y_BY]
        assert converted_block[1] == 1234

    def test_visitSetx(self):
        context = create_block_context(opcodes.MOTION_SET_X)
        testblock = context.block
        addInputOfType(testblock, "X", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_SET_X]
        assert converted_block[1] == 1234

    def test_visitSety(self):
        context = create_block_context(opcodes.MOTION_SET_Y)
        testblock = context.block
        addInputOfType(testblock, "Y", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_SET_Y]
        assert converted_block[1] == 1234

    def test_visitIfonedgebounce(self):
        context = create_block_context(opcodes.MOTION_BOUNCE_OFF_EDGE)
        testblock = context.block
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_BOUNCE_OFF_EDGE]

    def test_visitSetrotationstyle(self):
        context = create_block_context(opcodes.MOTION_SET_ROTATIONSTYLE)
        testblock = context.block
        testblock.fields["STYLE"] = ["teststyle"]

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_SET_ROTATIONSTYLE]
        assert converted_block[1] == "teststyle"

    def test_visitDirection(self):
        context = create_block_context(opcodes.MOTION_DIR)
        testblock = context.block

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_DIR]

    def test_visitXposition(self):
        context = create_block_context(opcodes.MOTION_X_POS)
        testblock = context.block

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_X_POS]

    def test_visitYposition(self):
        context = create_block_context(opcodes.MOTION_Y_POS)
        testblock = context.block

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_Y_POS]

    def test_visitGotoMenu(self):

        ## just test menu conversion
        context = create_block_context(opcodes.MOTION_GOTO_MENU)
        testblock = context.block
        addFieldOfType(testblock, "TO", AbstractType.MOTION)
        converted_block = visitBlock(context)
        assert converted_block[0] == AbstractInput.MOTION_RANDOM

        ## test menu and motion_goto block combination
        context = create_block_context(opcodes.MOTION_GOTO)
        add_menu_block(context, "motion_goto_menu", MenuTypes.TO, Types.TEST_MOTION)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.MOTION_GOTO]
        assert converted_block[1] == Types.TEST_MOTION


    def test_visitGlideToMenu(self):
        context = create_block_context(opcodes.MOTION_GLIDE_TO_MENU)
        testblock = context.block
        addFieldOfType(testblock, "TO", AbstractType.MOTION)
        converted_block = visitBlock(context)
        assert converted_block[0] == AbstractInput.MOTION_RANDOM

    def test_visitPointtowardsMenu(self):
        context = create_block_context(opcodes.MOTION_POINT_TOWARDS_MENU)
        testblock = context.block
        addFieldOfType(testblock, "TOWARDS", AbstractType.MOTION)
        converted_block = visitBlock(context)
        assert converted_block[0] == AbstractInput.MOTION_RANDOM

    ### Operator block testcases ###################
    def test_visitSubtract(self):
        context = create_block_context(opcodes.OPERATOR_SUBSTRACT)
        testblock = context.block
        addInputOfType(testblock, "NUM1", LiteralType.INT)
        addInputOfType(testblock, "NUM2", LiteralType.INT)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_SUBSTRACT]
        assert converted_block[1] == 1234
        assert converted_block[2] == 1234

    def test_visitGt(self):
        context = create_block_context(opcodes.OPERATOR_GREATER)
        testblock = context.block
        addInputOfType(testblock, "OPERAND1", LiteralType.INT)
        addInputOfType(testblock, "OPERAND2", LiteralType.INT)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_GREATER]
        assert converted_block[1] == 1234
        assert converted_block[2] == 1234

    def test_visitJoin(self):
        context = create_block_context(opcodes.OPERATOR_JOIN)
        testblock = context.block
        addInputOfType(testblock, "STRING1", LiteralType.STRING)
        addInputOfType(testblock, "STRING2", LiteralType.STRING)
        converted_block = visitBlock(context)
        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_JOIN]
        assert converted_block[1] == "teststring"
        assert converted_block[2] == "teststring"

    def test_visitLetterOf(self):
        context = create_block_context(opcodes.OPERATOR_LETTER_OF)
        testblock = context.block
        addInputOfType(testblock, "LETTER", LiteralType.STRING)
        addInputOfType(testblock, "STRING", LiteralType.STRING)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_LETTER_OF]
        assert converted_block[1] == "teststring"
        assert converted_block[2] == "teststring"

    def test_visitLt(self):
        context = create_block_context(opcodes.OPERATOR_LESS_THAN)
        testblock = context.block
        addInputOfType(testblock, "OPERAND1", LiteralType.INT)
        addInputOfType(testblock, "OPERAND2", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_LESS_THAN]
        assert converted_block[1] == 1234
        assert converted_block[2] == 1234

    def test_visitNot(self):
        context = create_block_context(opcodes.OPERATOR_NOT)
        testblock = context.block
        addInputOfType(testblock, "OPERAND", LiteralType.INT)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_NOT]
        assert converted_block[1] == 1234

    def test_visitMod(self):
        context = create_block_context(opcodes.OPERATOR_MODULO)
        testblock = context.block
        addInputOfType(testblock, "NUM1", LiteralType.INT)
        addInputOfType(testblock, "NUM2", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_MODULO]
        assert converted_block[1] == 1234
        assert converted_block[2] == 1234

    def test_visitAdd(self):
        context = create_block_context(opcodes.OPERATOR_ADD)
        testblock = context.block
        addInputOfType(testblock, "NUM1", LiteralType.INT)
        addInputOfType(testblock, "NUM2", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_ADD]
        assert converted_block[1] == 1234
        assert converted_block[2] == 1234

    def test_visitEquals(self):
        context = create_block_context(opcodes.OPERATOR_EQUALS)
        testblock = context.block
        addInputOfType(testblock, "OPERAND1", LiteralType.INT)
        addInputOfType(testblock, "OPERAND2", LiteralType.INT)
        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_EQUALS]
        assert converted_block[1] == 1234
        assert converted_block[2] == 1234

    def test_visitMathop(self):
        context = create_block_context(opcodes.OPERATOR_MATH_OP)
        testblock = context.block
        addInputOfType(testblock, "NUM", LiteralType.INT)
        testblock.fields["OPERATOR"] = ["testoperator"]

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_MATH_OP]
        assert converted_block[1] == "testoperator"
        assert converted_block[2] == 1234

    def test_visitAnd(self):
        context = create_block_context(opcodes.OPERATOR_AND)
        testblock = context.block
        addInputOfType(testblock, "OPERAND1", LiteralType.INT)
        addInputOfType(testblock, "OPERAND2", LiteralType.INT)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_AND]
        assert converted_block[1] == 1234
        assert converted_block[2] == 1234

    def test_visitRound(self):
        context = create_block_context(opcodes.OPERATOR_ROUND)
        testblock = context.block
        addInputOfType(testblock, "NUM", LiteralType.INT)

        converted_block = visitBlock(context)

        assert converted_block[0] == "rounded"
        assert converted_block[1] == 1234

    def test_visitMultiply(self):
        context = create_block_context(opcodes.OPERATOR_MULTIPLY)
        testblock = context.block
        addInputOfType(testblock, "NUM1", LiteralType.INT)
        addInputOfType(testblock, "NUM2", LiteralType.INT)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_MULTIPLY]
        assert converted_block[1] == 1234
        assert converted_block[2] == 1234

    def test_visitRandom(self):
        context = create_block_context(opcodes.OPERATOR_RANDOM)
        testblock = context.block
        addInputOfType(testblock, "FROM", LiteralType.INT)
        addInputOfType(testblock, "TO", LiteralType.INT)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_RANDOM]
        assert converted_block[1] == 1234
        assert converted_block[2] == 1234

    def test_visitDivide(self):
        context = create_block_context(opcodes.OPERATOR_DIVIDE)
        testblock = context.block
        addInputOfType(testblock, "NUM1", LiteralType.INT)
        addInputOfType(testblock, "NUM2", LiteralType.INT)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_DIVIDE]
        assert converted_block[1] == 1234
        assert converted_block[2] == 1234

    def test_visitContains(self):
        context = create_block_context(opcodes.OPERATOR_CONTAINS)
        testblock = context.block
        addInputOfType(testblock, "STRING1", LiteralType.STRING)
        addInputOfType(testblock, "STRING2", LiteralType.STRING)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_CONTAINS]
        assert converted_block[1] == "teststring"
        assert converted_block[2] == "teststring"

    def test_visitOr(self):
        context = create_block_context(opcodes.OPERATOR_OR)
        testblock = context.block
        addInputOfType(testblock, "OPERAND1", LiteralType.INT)
        addInputOfType(testblock, "OPERAND2", LiteralType.INT)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_OR]
        assert converted_block[1] == 1234
        assert converted_block[2] == 1234

    def test_visitLength(self):
        context = create_block_context(opcodes.OPERATOR_LENGTH)
        testblock = context.block
        addInputOfType(testblock, "STRING", LiteralType.STRING)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.OPERATOR_LENGTH]
        assert converted_block[1] == "teststring"

    def test_visit_literal(self):
        test_list = [4, "10-"]
        test_list2 = [12, "Test2"]
        test_list3 = [13, "Test3"]
        test_list4 = [5, "Test4"]
        test_list5 = [5, None]
        test_list6 = [9, "Test6"]


        test_float = visitLiteral(test_list)
        test_twelve = visitLiteral(test_list2)
        test_thirteen = visitLiteral(test_list3)
        test_five = visitLiteral(test_list4)
        test_five_none = visitLiteral(test_list5)
        test_nine = visitLiteral(test_list6)

        assert test_float == "10-"
        assert test_twelve == ["readVariable", "Test2"]
        assert test_thirteen == ["contentsOfList:", "Test3"]
        assert test_five == "Test4"
        assert test_five_none == 0
        assert test_nine == "Test6"


    ### Unsupported block testcase ###################
    def test_unsupportedBlock(self):
        context = create_block_context(opcodes.NOT_SUPPORTED)
        testblock = context.block
        addInputOfType(testblock, "STRING", LiteralType.STRING)

        converted_block = visitBlock(context)

        assert converted_block[0] == opcodes.opcode_map[opcodes.NOT_SUPPORTED]
        assert converted_block[1] == "ERROR: BLOCK NOT FOUND: not_supported_block"


if __name__ == "__main__":
    unittest.main()


