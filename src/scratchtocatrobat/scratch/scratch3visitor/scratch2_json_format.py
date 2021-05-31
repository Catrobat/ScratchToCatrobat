# This file contains every information I could gather for scratch2/scratch3 projects
# and any links I could find, documenting the mappings and value enums

# https://en.scratch-wiki.info/wiki/Scratch_File_Format
# https://github.com/LLK/scratch-vm/tree/develop/src/blocks scratch3.0 opcodes can be found here
# https://en.scratch-wiki.info/wiki/Scratch_File_Format_(2.0)/Block_Selectors scratch2.0 opcodes
# https://en.scratch-wiki.info/wiki/List_of_Block_Workarounds
class Scratch3_2Opcodes(object):
    # events #
    FLAG_CLICKED = "event_whenflagclicked"
    BROADCAST = "event_broadcast"
    BROADCAST_AND_WAIT = "event_broadcastandwait"
    SPRITE_CLICKED = "event_whenthisspriteclicked"
    KEY_PRESSED = "event_whenkeypressed"
    BACKDROP_SWITCHED_TO = "event_whenbackdropswitchesto"
    BROADCAST_RECEIVED = "event_whenbroadcastreceived"
    GREATER_THAN = "event_whengreaterthan"

    # looks #
    LOOKS_SHOW = "looks_show"
    LOOKS_FORWARD_BACKWARD_LAYERS = "looks_goforwardbackwardlayers"
    LOOKS_SAY_FOR_SECS = "looks_sayforsecs"
    LOOKS_SAY = "looks_say"
    LOOKS_THINK_FOR_SECS = "looks_thinkforsecs"
    LOOKS_THINK = "looks_think"
    LOOKS_SWITCH_COSTUME_TO = "looks_switchcostumeto"
    LOOKS_NEXT_COSTUME = "looks_nextcostume"
    LOOKS_NEXT_BACKDROP = "looks_nextbackdrop"
    LOOKS_SWITCH_BACKDROP_TO = "looks_switchbackdropto"
    LOOKS_CHANGE_SIZE_BY = "looks_changesizeby"
    LOOKS_SET_SIZE_TO = "looks_setsizeto"
    LOOKS_CHANGE_EFFECT_BY = "looks_changeeffectby"
    LOOKS_SET_EFFECT_TO = "looks_seteffectto"
    LOOKS_CLEAR_EFFECTS = "looks_cleargraphiceffects"
    LOOKS_HIDE = "looks_hide"
    LOOKS_GOTO_FRONT_BACK = "looks_gotofrontback"
    LOOKS_SIZE = "looks_size"
    LOOKS_COSTUME = "looks_costume"
    LOOKS_BACKDROPS = "looks_backdrops"
    LOOKS_COSTUME_NUMBER_NAME = "looks_costumenumbername"
    LOOKS_BACK_DROP_NUMBER_NAME = "looks_backdropnumbername"

    # sounds #
    SOUNDS_PLAY = "sound_play"
    SOUNDS_PLAY_UNTIL_DONE = "sound_playuntildone"
    SOUNDS_STOP_ALL = "sound_stopallsounds"
    SOUNDS_CLEAR = "sound_cleareffects"
    SOUNDS_CHANGE_VOLUME_BY = "sound_changevolumeby"
    SOUNDS_SET_VOLUME_TO = "sound_setvolumeto"
    SOUNDS_VOLUME = "sound_volume"
    SOUNDS_MENU = "sound_sounds_menu"

    # sensing #
    SENSING_TOUCHING_OBJECT = "sensing_touchingobject"
    SENSING_ASK_AND_WAIT = "sensing_askandwait"
    SENSING_SET_DRAG_MODE = "sensing_setdragmode"
    SENSING_RESET_TIMER = "sensing_resettimer"
    SENSING_LOUDNESS = "sensing_loudness"
    SENSING_DISTANCE_TO = "sensing_distanceto"
    SENSING_COLOR_TOUCHING_COLOR = "sensing_coloristouchingcolor"
    SENSING_TO_DISTANCE_MENU = "sensing_distancetomenu" # no mapping to scratch2
    SENSING_OF = "sensing_of"
    SENSING_CURRENT = "sensing_current"
    SENSING_CURRENT_MENU = "sensing_currentmenu" # no mapping to scratch2
    SENSING_ANSWER = "sensing_answer"
    SENSING_DAYS_SINCE_2000 = "sensing_dayssince2000"
    SENSING_KEYPRESSED = "sensing_keypressed"
    SENSING_KEY_OPTIONS = "sensing_keyoptions" # no mapping to scratch2
    SENSING_MOUSEX = "sensing_mousex"
    SENSING_MOUSE_DOWN = "sensing_mousedown"
    SENSING_MOUSEY = "sensing_mousey"
    SENSING_TIMER = "sensing_timer"
    SENSING_TOUCHING_COLOR = "sensing_touchingcolor"
    SENSING_USERNAME = "sensing_username"
    SENSING_TOUCHING_OBJECT_MENU = "sensing_touchingobjectmenu"
    SENSING_OF_OBJECT_MENU = "sensing_of_object_menu"

    # data #
    DATA_SET_VARIABLE_TO = "data_setvariableto"
    DATA_CHANGE_VARIABLE_BY = "data_changevariableby"
    DATA_SHOW_VARIABLE = "data_showvariable"
    DATA_HIDE_VARIABLE = "data_hidevariable"
    DATA_ADD_TO_LIST = "data_addtolist"
    DATA_DELETE_OF_LIST = "data_deleteoflist"
    DATA_INSERT_AT_LIST = "data_insertatlist"
    DATA_REPLACE_ITEM_OF_LIST = "data_replaceitemoflist"
    DATA_ITEM_OF_LIST = "data_itemoflist"
    DATA_ITEMNUM_OF_LIST = "data_itemnumoflist"
    DATA_LENGTH_OF_LIST = "data_lengthoflist"
    DATA_LIST_CONTAINS_ITEM = "data_listcontainsitem"
    DATA_SHOW_LIST = "data_showlist"
    DATA_HIDE_LIST = "data_hidelist"
    DATA_CONTENTS_OF_LIST = "data_contentsoflist"

    # control #
    CONTROL_WAIT = "control_wait"
    CONTROL_REPEAT = "control_repeat"
    CONTROL_IF = "control_if"
    CONTROL_IF_ELSE = "control_if_else"
    CONTROL_WAIT_UNTIL = "control_wait_until"
    CONTROL_REPEAT_UNTIL = "control_repeat_until"
    CONTROL_CREATE_CLONE_OF = "control_create_clone_of"
    CONTROL_CREATE_CLONE_OF_MENU = "control_create_clone_of_menu"
    CONTROL_STOP = "control_stop"
    CONTROL_START_AS_CLONE = "control_start_as_clone"
    CONTROL_DELETE_THIS_CLONE = "control_delete_this_clone"
    CONTROL_FOREVER = "control_forever"
    CONTROL_PROCEDURES_CALL = "procedures_call"
    CONTROL_PROCEDURES_PROTOTYPE = "procedures_prototype"
    CONTROL_ARGUMENT_REPORTER_BOOL = "argument_reporter_boolean"
    CONTROL_ARGUMENT_REPORTER_STRING = "argument_reporter_string_number"
    CONTROL_PROCEDURES_DEFINITION = "procedures_definition"


    # pen #
    PEN_CLEAR = "pen_clear"
    PEN_STAMP = "pen_stamp"
    PEN_DOWN = "pen_penDown"
    PEN_UP = "pen_penUp"
    PEN_SET_COLOR = "pen_setPenColorToColor"
    PEN_SET_PARAM = "pen_setPenColorParamTo"
    PEN_CHANGE_COLOR = "pen_changePenColorParamBy"
    PEN_SET_SIZE = "pen_setPenSizeTo"
    PEN_CHANGE_SIZE = "pen_changePenSizeBy"
    PEN_COLOR_PARAM_MENU = "pen_menu_colorParam"
    PEN_SET_SHADE_TO_NUMBER = "pen_setPenShadeToNumber"
    PEN_CHANGE_PEN_SHADE_BY = "pen_changePenShadeBy"
    PEN_SET_PEN_HUE_TO_NUMBER = "pen_setPenHueToNumber"

    # motion #
    MOTION_MOVE_STEPS = "motion_movesteps"
    MOTION_TURN_RIGHT = "motion_turnright"
    MOTION_TURN_LEFT = "motion_turnleft"
    MOTION_GOTO_XY = "motion_gotoxy"
    MOTION_GOTO = "motion_goto"
    MOTION_GLIDE_TO = "motion_glideto"
    MOTION_GLIDE_SECS_TO_XY = "motion_glidesecstoxy"
    MOTION_POINT_IN_DIR = "motion_pointindirection"
    MOTION_POINT_TOWARDS = "motion_pointtowards"
    MOTION_CHANGE_BY_XY = "motion_changexby"
    MOTION_CHANGE_Y_BY = "motion_changeyby"
    MOTION_SET_X = "motion_setx"
    MOTION_SET_Y = "motion_sety"
    MOTION_BOUNCE_OFF_EDGE = "motion_ifonedgebounce"
    MOTION_SET_ROTATIONSTYLE = "motion_setrotationstyle"
    MOTION_DIR = "motion_direction"
    MOTION_X_POS = "motion_xposition"
    MOTION_Y_POS = "motion_yposition"
    MOTION_GOTO_MENU = "motion_goto_menu"
    MOTION_GLIDE_TO_MENU = "motion_glideto_menu"
    MOTION_POINT_TOWARDS_MENU = "motion_pointtowards_menu"

    # operator #
    OPERATOR_SUBSTRACT = "operator_subtract"
    OPERATOR_GREATER = "operator_gt"
    OPERATOR_JOIN = "operator_join"
    OPERATOR_LETTER_OF = "operator_letter_of"
    OPERATOR_LESS_THAN = "operator_lt"
    OPERATOR_NOT = "operator_not"
    OPERATOR_MODULO = "operator_mod"
    OPERATOR_ADD = "operator_add"
    OPERATOR_EQUALS = "operator_equals"
    OPERATOR_MATH_OP = "operator_mathop"
    OPERATOR_AND = "operator_and"
    OPERATOR_ROUND = "operator_round"
    OPERATOR_MULTIPLY = "operator_multiply"
    OPERATOR_RANDOM = "operator_random"
    OPERATOR_DIVIDE = "operator_divide"
    OPERATOR_CONTAINS = "operator_contains"
    OPERATOR_OR = "operator_or"
    OPERATOR_LENGTH = "operator_length"

    # not supported block #
    NOT_SUPPORTED = "not_supported_block"

    # Maps Scratch3 Opcodes from above to Scratch2 Opcodes
    opcode_map = {
        ### event opcodes ####
        FLAG_CLICKED: "whenGreenFlag",
        BROADCAST: "broadcast:",
        BROADCAST_AND_WAIT: "doBroadcastAndWait",
        SPRITE_CLICKED: "whenClicked",
        KEY_PRESSED: "whenKeyPressed",
        BACKDROP_SWITCHED_TO: "whenSceneStarts",
        BROADCAST_RECEIVED: "whenIReceive",
        GREATER_THAN: "whenSensorGreaterThan",

        ### looks opcodes ####
        LOOKS_SHOW: "show",
        LOOKS_FORWARD_BACKWARD_LAYERS: "goBackByLayers:",
        LOOKS_SAY_FOR_SECS: "say:duration:elapsed:from:",
        LOOKS_SAY: "say:",
        LOOKS_THINK_FOR_SECS: "think:duration:elapsed:from:",
        LOOKS_THINK: "think:",
        LOOKS_SWITCH_COSTUME_TO: "lookLike:",
        LOOKS_NEXT_COSTUME: "nextCostume",
        LOOKS_NEXT_BACKDROP : "nextCostume",
        LOOKS_SWITCH_BACKDROP_TO: "startScene",
        LOOKS_CHANGE_SIZE_BY: "changeSizeBy:",
        LOOKS_SET_SIZE_TO: "setSizeTo:",
        LOOKS_CHANGE_EFFECT_BY: "changeGraphicEffect:by:",
        LOOKS_SET_EFFECT_TO: "setGraphicEffect:to:",
        LOOKS_CLEAR_EFFECTS: "filterReset",
        LOOKS_HIDE: "hide",
        LOOKS_GOTO_FRONT_BACK: "comeToFront",
        LOOKS_SIZE: "scale",
        LOOKS_COSTUME_NUMBER_NAME + "_name": "costumeName",
        LOOKS_COSTUME_NUMBER_NAME + "_number": "costumeIndex",

        ### sounds opcodes ###
        SOUNDS_PLAY: "playSound:",
        SOUNDS_PLAY_UNTIL_DONE: "doPlaySoundAndWait",
        SOUNDS_STOP_ALL: "stopAllSounds",
        SOUNDS_CLEAR: "clearSoundEffects",
        SOUNDS_CHANGE_VOLUME_BY: "changeVolumeBy:",
        SOUNDS_SET_VOLUME_TO: "setVolumeTo:",
        SOUNDS_VOLUME: "volume",

        ### sensing opcodes
        SENSING_TOUCHING_OBJECT: "touching:",
        SENSING_ASK_AND_WAIT: "doAsk",
        SENSING_SET_DRAG_MODE: "dragMode",
        SENSING_RESET_TIMER: "timerReset",
        SENSING_LOUDNESS: "soundLevel",
        SENSING_DISTANCE_TO: "distanceTo:",
        SENSING_COLOR_TOUCHING_COLOR: "touchingColor:",
        SENSING_OF: "getAttribute:of:",
        SENSING_CURRENT: "timeAndDate",
        SENSING_ANSWER: "answer",
        SENSING_DAYS_SINCE_2000: "timestamp",
        SENSING_KEYPRESSED: "keyPressed:",
        SENSING_MOUSEX: "mouseX",
        SENSING_MOUSE_DOWN: "mousePressed",
        SENSING_MOUSEY: "mouseY",
        SENSING_TIMER: "timer",
        SENSING_TOUCHING_COLOR: "touchingColor:",
        SENSING_USERNAME: "getUserName",

        ### data opcodes
        DATA_SET_VARIABLE_TO: "setVar:to:",
        DATA_CHANGE_VARIABLE_BY: "changeVar:by:",
        DATA_SHOW_VARIABLE: "showVariable:",
        DATA_HIDE_VARIABLE: "hideVariable:",
        DATA_ADD_TO_LIST: "append:toList:",
        DATA_DELETE_OF_LIST: "deleteLine:ofList:",
        DATA_INSERT_AT_LIST: "insert:at:ofList:",
        DATA_REPLACE_ITEM_OF_LIST: "setLine:ofList:to:",
        DATA_ITEM_OF_LIST: "getLine:ofList:",
        DATA_ITEMNUM_OF_LIST: "itemNum:ofList:",
        DATA_LENGTH_OF_LIST: "lineCountOfList:",
        DATA_LIST_CONTAINS_ITEM: "list:contains:",
        DATA_SHOW_LIST: "showList:",
        DATA_HIDE_LIST: "hideList:",
        DATA_CONTENTS_OF_LIST: "contentsOfList:",

        ### control opcodes ###
        CONTROL_WAIT: "wait:elapsed:from:",
        CONTROL_REPEAT: "doRepeat",
        CONTROL_IF: "doIf",
        CONTROL_IF_ELSE: "doIfElse",
        CONTROL_WAIT_UNTIL: "doWaitUntil",
        CONTROL_REPEAT_UNTIL: "doUntil",
        CONTROL_CREATE_CLONE_OF: "createCloneOf",
        CONTROL_STOP: "stopScripts",
        CONTROL_START_AS_CLONE: "whenCloned",
        CONTROL_DELETE_THIS_CLONE: "deleteClone",
        CONTROL_FOREVER: "doForever",
        CONTROL_PROCEDURES_CALL: "call",
        CONTROL_PROCEDURES_PROTOTYPE: "procDef",
        CONTROL_ARGUMENT_REPORTER_BOOL: "getParam",
        CONTROL_ARGUMENT_REPORTER_STRING: "getParam",


        ### pen opcodes ###
        PEN_CLEAR: "clearPenTrails",
        PEN_STAMP: "stampCostume",
        PEN_DOWN: "putPenDown",
        PEN_UP: "putPenUp",
        PEN_SET_COLOR: "penColor:",
        PEN_SET_PARAM: "setPenParamTo:",
        PEN_CHANGE_COLOR: "changePenParamBy:",
        PEN_SET_SIZE: "penSize:",
        PEN_CHANGE_SIZE: "changePenSizeBy:",
        PEN_SET_SHADE_TO_NUMBER : "penShade:",
        PEN_CHANGE_PEN_SHADE_BY: "changePenShadeBy:",
        PEN_SET_PEN_HUE_TO_NUMBER: "penHue:",

        ### motion opcodes ###
        MOTION_MOVE_STEPS: "forward:",
        MOTION_TURN_RIGHT: "turnRight:",
        MOTION_TURN_LEFT: "turnLeft:",
        MOTION_GOTO_XY: "gotoX:y:",
        MOTION_GOTO: "gotoSpriteOrMouse:",
        MOTION_GLIDE_TO: "glideTo:",
        MOTION_GLIDE_SECS_TO_XY: "glideSecs:toX:y:elapsed:from:",
        MOTION_POINT_IN_DIR: "heading:",
        MOTION_POINT_TOWARDS: "pointTowards:",
        MOTION_CHANGE_BY_XY: "changeXposBy:",
        MOTION_CHANGE_Y_BY: "changeYposBy:",
        MOTION_SET_X: "xpos:",
        MOTION_SET_Y: "ypos:",
        MOTION_BOUNCE_OFF_EDGE: "bounceOffEdge",
        MOTION_SET_ROTATIONSTYLE: "setRotationStyle",
        MOTION_DIR: "heading",
        MOTION_X_POS: "xpos",
        MOTION_Y_POS: "ypos",

        ### operator opcodes ###
        OPERATOR_SUBSTRACT: "-",
        OPERATOR_GREATER: ">",
        OPERATOR_JOIN: "concatenate:with:",
        OPERATOR_LETTER_OF: "letter:of:",
        OPERATOR_LESS_THAN: "<",
        OPERATOR_NOT: "not",
        OPERATOR_MODULO: "%",
        OPERATOR_ADD: "+",
        OPERATOR_EQUALS: "=",
        OPERATOR_MATH_OP: "computeFunction:of:",
        OPERATOR_AND: "&",
        OPERATOR_ROUND: "rounded",
        OPERATOR_MULTIPLY: "*",
        OPERATOR_RANDOM: "randomFrom:to:",
        OPERATOR_DIVIDE: "/",
        OPERATOR_CONTAINS: "contains:",
        OPERATOR_OR: "|",
        OPERATOR_LENGTH: "stringLength:",

        ### not suported block ###
        NOT_SUPPORTED: "note:",
    }


class AppliedBlockNumbers(object):
    # Definitions of those Applied Block numbers can be found here:
    # https://en.scratch-wiki.info/wiki/Scratch_File_Format
    # Just check under "blocks"
    Number = 4
    PositiveNumber = 5
    PositiveInteger = 6
    Integer = 7
    Angle = 8
    Color = 9
    String = 10
    Broadcast = 11
    Variable = 12
    List = 13


class MenuTypes(object):
    TO = "TO"
    SOUND_MENU = "SOUND_MENU"
    CLONE_MENU = "CLONE_OPTION"
    DISTANCE_TO_MENU = "DISTANCETOMENU"
    COSTUME = "COSTUME"
    BACKDROP = "BACKDROP"
    NUMBER_NAME = "NUMBER_NAME"
    DURATION = "DURATION"
    PARAM_VALUE = "VALUE"
    CURRENT_MENU = "CURRENTMENU"
    TOUCHING_OBJECT = "TOUCHINGOBJECTMENU"
    OBJECT = "OBJECT"
    COLOR_PARAM = "colorParam"


class InputTypes(object):
    BROADCAST_INPUT = "BROADCAST_INPUT"
    DURATION_INPUT = "DURATION"
    MUTATION = "MUTATION" # note that in real scratch projects this will just be an ID.
    CONDITION = "CONDITION"
    SUBSTACK = "SUBSTACK"
    MESSAGE = "MESSAGE"
    COLOR_PARAM = "COLOR_PARAM"
    COLOR = "COLOR"
    SHADE = "SHADE"
    HUE = "HUE"
    VALUE = "VALUE"


class FieldTypes(object):
    PROPERTY = "PROPERTY"
    KEY_OPTION = "KEY_OPTION"
    BACKDROP = "BACKDROP"
    BROADCAST_OPTION = "BROADCAST_OPTION"
    WHEN_GREATER_THAN_MENU = "WHENGREATERTHANMENU"


class ProcedureTypes(object):
    MUTATION = "mutation"
    DEFAULT_PROCCODE = "blockname"
    DEFINTION = "custom_block"


class Modifier(object):
    STRING_OR_NUMBER = "%s"
    BOOLEAN = "%b"


class Defaults(object):
    PARAM_BOOLEAN = "false"
    PARAM_STRING = ""
    REPORTER = 'r'
    WARP = False