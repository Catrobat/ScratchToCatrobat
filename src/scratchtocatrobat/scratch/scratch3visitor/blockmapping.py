import looks, motion, event, sensing, sound, operator, control, data, pen
from scratchtocatrobat.scratch.scratch3visitor.scratch2_json_format import Scratch3_2Opcodes as opcodes

visitormap = {
    ### event blocks ####
    opcodes.FLAG_CLICKED: event.visitWhenflagclicked,  # tested
    opcodes.BROADCAST: event.visitBroadcast,  # tested
    opcodes.BROADCAST_AND_WAIT: event.visitBroadcastandwait,  # tested
    opcodes.KEY_PRESSED: event.visitWhenkeypressed,  # tested
    opcodes.SPRITE_CLICKED: event.visitWhenthisspriteclicked,  # tested
    opcodes.GREATER_THAN: event.visitWhengreaterthan,  # tested
    opcodes.BACKDROP_SWITCHED_TO: event.visitWhenbackdropswitchesto,  # tested
    opcodes.BROADCAST_RECEIVED: event.visitWhenbroadcastreceived,  # tested

    ### motion blocks ####
    opcodes.MOTION_MOVE_STEPS: motion.visitMovesteps,  # tested
    opcodes.MOTION_TURN_RIGHT: motion.visitTurnright,  # tested
    opcodes.MOTION_TURN_LEFT: motion.visitTurnleft,  # tested
    opcodes.MOTION_GOTO: motion.visitGoto,  # tested
    opcodes.MOTION_GOTO_XY: motion.visitGotoxy,  # tested
    opcodes.MOTION_GLIDE_TO: motion.visitGlideto,  # tested
    opcodes.MOTION_GLIDE_SECS_TO_XY: motion.visitGlidesecstoxy,  # tested
    opcodes.MOTION_POINT_IN_DIR: motion.visitPointindirection,  # tested
    opcodes.MOTION_POINT_TOWARDS: motion.visitPointtowards,  # tested
    opcodes.MOTION_CHANGE_BY_XY: motion.visitChangexby,  # tested
    opcodes.MOTION_SET_X: motion.visitSetx,  # tested
    opcodes.MOTION_CHANGE_Y_BY: motion.visitChangeyby,  # tested
    opcodes.MOTION_SET_Y: motion.visitSety,  # tested
    opcodes.MOTION_BOUNCE_OFF_EDGE: motion.visitIfonedgebounce,  # tested
    opcodes.MOTION_SET_ROTATIONSTYLE: motion.visitSetrotationstyle,  # tested
    opcodes.MOTION_GOTO_MENU: motion.visitGoto_menu,  # tested
    opcodes.MOTION_GLIDE_TO_MENU: motion.visitGlideto_menu,  # tested
    opcodes.MOTION_POINT_TOWARDS_MENU: motion.visitPointtowards_menu,  # tested
    opcodes.MOTION_DIR: motion.visitDirection,  # tested
    opcodes.MOTION_Y_POS: motion.visitYposition,  # tested
    opcodes.MOTION_X_POS: motion.visitXposition,  # tested

    ### look blocks ####
    opcodes.LOOKS_SAY_FOR_SECS: looks.visitSayforsecs,  # tested
    opcodes.LOOKS_SAY: looks.visitSay,  # tested
    opcodes.LOOKS_THINK_FOR_SECS: looks.visitThinkforsecs,  # tested
    opcodes.LOOKS_THINK: looks.visitThink,  # tested
    opcodes.LOOKS_SWITCH_COSTUME_TO: looks.visitSwitchcostumeto,  # tested
    opcodes.LOOKS_NEXT_COSTUME: looks.visitNextcostume,  # tested
    opcodes.LOOKS_SWITCH_BACKDROP_TO: looks.visitSwitchbackdropto,  # tested
    opcodes.LOOKS_NEXT_BACKDROP: looks.visitNextbackdrop,  # tested
    opcodes.LOOKS_CHANGE_SIZE_BY: looks.visitChangesizeby,  # tested
    opcodes.LOOKS_SET_SIZE_TO: looks.visitSetsizeto,  # tested
    opcodes.LOOKS_CHANGE_EFFECT_BY: looks.visitChangeeffectby,  # tested
    opcodes.LOOKS_SET_EFFECT_TO: looks.visitSeteffectto,  # tested
    opcodes.LOOKS_CLEAR_EFFECTS: looks.visitCleargraphiceffects,  # tested
    opcodes.LOOKS_SHOW: looks.visitShow,  # tested
    opcodes.LOOKS_HIDE: looks.visitHide,  # tested
    opcodes.LOOKS_GOTO_FRONT_BACK: looks.visitGotofrontback,  # tested
    opcodes.LOOKS_FORWARD_BACKWARD_LAYERS: looks.visitGoforwardbackwardlayers,  # tested by fleischhacker
    opcodes.LOOKS_COSTUME: looks.visitCostume,  # tested
    opcodes.LOOKS_BACKDROPS: looks.visitBackdrops,  # tested
    opcodes.LOOKS_COSTUME_NUMBER_NAME: looks.visitCostumenumbername,  # tested
    opcodes.LOOKS_SIZE: looks.visitSize,  # tested
    opcodes.LOOKS_BACK_DROP_NUMBER_NAME: looks.visitBackdropnumbername,

    ### sound blocks ####
    opcodes.SOUNDS_PLAY: sound.visitPlay,  # tested
    opcodes.SOUNDS_PLAY_UNTIL_DONE: sound.visitPlayuntildone,  # tested
    opcodes.SOUNDS_STOP_ALL: sound.visitStopallsounds,  # tested
    "sound_changeeffectby": sound.visitChangeeffectby,  # TODO not implemented in catrobat yet
    "sound_seteffectto": sound.visitSeteffectto,  # TODO not implemented in catrobat yet
    "sound_cleareffects": sound.visitCleareffects,  # TODO not implemented in scratch2, workaroundq
    opcodes.SOUNDS_CHANGE_VOLUME_BY: sound.visitChangevolumeby,  # tested
    opcodes.SOUNDS_SET_VOLUME_TO: sound.visitSetvolumeto,  # tested
    opcodes.SOUNDS_MENU: sound.visitSounds_menu,  # tested
    opcodes.SOUNDS_VOLUME: sound.visitVolume,  # tested

    ### control blocks ####
    opcodes.CONTROL_WAIT: control.visitWait,  # tested
    opcodes.CONTROL_REPEAT: control.visitRepeat,  # tested
    opcodes.CONTROL_IF: control.visitIf,  # tested
    opcodes.CONTROL_IF_ELSE: control.visitIf_else,  # tested
    opcodes.CONTROL_WAIT_UNTIL: control.visitWait_until,  # tested
    opcodes.CONTROL_REPEAT_UNTIL: control.visitRepeat_until,  # tested
    opcodes.CONTROL_CREATE_CLONE_OF: control.visitCreate_clone_of,  # tested
    opcodes.CONTROL_CREATE_CLONE_OF_MENU: control.visitCreate_clone_of_menu,  # tested
    opcodes.CONTROL_STOP: control.visitStop,  # tested
    opcodes.CONTROL_START_AS_CLONE: control.visitStart_as_clone,  # tested
    opcodes.CONTROL_FOREVER: control.visitForever,  # tested
    opcodes.CONTROL_DELETE_THIS_CLONE: control.visitDelete_this_clone,  # tested
    opcodes.CONTROL_PROCEDURES_CALL: control.visitProcedures_call,  # tested
    opcodes.CONTROL_PROCEDURES_DEFINITION: control.visitProcedures_definition,  # tested
    opcodes.CONTROL_ARGUMENT_REPORTER_STRING: control.visitArgumentIntOrString,  # tested
    opcodes.CONTROL_ARGUMENT_REPORTER_BOOL: control.visitArgumentBool,  # tested
    opcodes.CONTROL_PROCEDURES_PROTOTYPE: control.visitProcedures_prototype,  # tested

    ### sensing blocks ####
    opcodes.SENSING_ASK_AND_WAIT: sensing.visitAskandwait,  # tested
    opcodes.SENSING_SET_DRAG_MODE: sensing.visitSetdragmode,  # tested
    opcodes.SENSING_RESET_TIMER: sensing.visitResettimer,  # tested
    opcodes.SENSING_DISTANCE_TO: sensing.visitDistanceto,  # tested
    opcodes.SENSING_TO_DISTANCE_MENU: sensing.visitDistanceto_menu,  # tested
    opcodes.SENSING_LOUDNESS: sensing.visitLoudness,  # tested
    opcodes.SENSING_COLOR_TOUCHING_COLOR: sensing.visitColoristouchingcolor,  # tested
    opcodes.SENSING_OF: sensing.visitOf,  # tested
    opcodes.SENSING_CURRENT: sensing.visitCurrent,  # tested
    opcodes.SENSING_ANSWER: sensing.visitAnswer,  # tested
    opcodes.SENSING_DAYS_SINCE_2000: sensing.visitDayssince2000,  # tested
    opcodes.SENSING_KEYPRESSED: sensing.visitKeypressed,  # tested
    opcodes.SENSING_KEY_OPTIONS: sensing.visitKey_options,
    opcodes.SENSING_MOUSEX: sensing.visitMousex,  # tested
    opcodes.SENSING_MOUSE_DOWN: sensing.visitMousedown,  # tested
    opcodes.SENSING_MOUSEY: sensing.visitMousey,  # tested
    opcodes.SENSING_TIMER: sensing.visitTimer,  # tested
    opcodes.SENSING_TOUCHING_COLOR: sensing.visitTouchingcolor,  # tested
    opcodes.SENSING_TOUCHING_OBJECT: sensing.visitTouchingObject,  # tested
    opcodes.SENSING_CURRENT_MENU: sensing.visitCurrent_menu,  # tested
    opcodes.SENSING_TOUCHING_OBJECT_MENU: sensing.visitTouchingObjectMenu,  # tested
    opcodes.SENSING_USERNAME: sensing.visitUsername,  # tested
    opcodes.SENSING_OF_OBJECT_MENU: sensing.visitOf_object_menu,  # tested

    ### operator blocks ####
    opcodes.OPERATOR_SUBSTRACT: operator.visitSubtract,  # tested
    opcodes.OPERATOR_GREATER: operator.visitGt,  # tested
    opcodes.OPERATOR_JOIN: operator.visitJoin,  # tested
    opcodes.OPERATOR_LETTER_OF: operator.visitLetter_of,  # tested
    opcodes.OPERATOR_LESS_THAN: operator.visitLt,  # tested
    opcodes.OPERATOR_NOT: operator.visitNot,  # tested
    opcodes.OPERATOR_MODULO: operator.visitMod,  # tested
    opcodes.OPERATOR_ADD: operator.visitAdd,  # tested
    opcodes.OPERATOR_EQUALS: operator.visitEquals,  # tested
    opcodes.OPERATOR_MATH_OP: operator.visitMathop,  # tested
    opcodes.OPERATOR_AND: operator.visitAnd,  # tested
    opcodes.OPERATOR_ROUND: operator.visitRound,  # tested
    opcodes.OPERATOR_MULTIPLY: operator.visitMultiply,  # tested
    opcodes.OPERATOR_RANDOM: operator.visitRandom,  # tested
    opcodes.OPERATOR_DIVIDE: operator.visitDivide,  # tested
    opcodes.OPERATOR_CONTAINS: operator.visitContains,  # tested
    opcodes.OPERATOR_OR: operator.visitOr,  # tested
    opcodes.OPERATOR_LENGTH: operator.visitLength,  # tested

    ### data blocks ####
    opcodes.DATA_ADD_TO_LIST: data.visitAddtolist,  # tested
    opcodes.DATA_DELETE_OF_LIST: data.visitDeleteoflist,  # tested
    opcodes.DATA_INSERT_AT_LIST: data.visitInsertatlist,  # tested
    opcodes.DATA_REPLACE_ITEM_OF_LIST: data.visitReplaceitemoflist,  # tested
    opcodes.DATA_ITEM_OF_LIST: data.visitItemoflist,  # tested
    opcodes.DATA_ITEMNUM_OF_LIST: data.visitItemnumoflist,  # tested
    opcodes.DATA_LENGTH_OF_LIST: data.visitLengthoflist,  # tested
    opcodes.DATA_LIST_CONTAINS_ITEM: data.visitListcontainsitem,  # tested
    opcodes.DATA_SHOW_LIST: data.visitShowlist,  # tested
    opcodes.DATA_HIDE_LIST: data.visitHidelist,  # tested
    opcodes.DATA_CONTENTS_OF_LIST: data.visitContentsoflist,  # tested
    opcodes.DATA_SET_VARIABLE_TO: data.visitSetvariableto,  # tested
    opcodes.DATA_CHANGE_VARIABLE_BY: data.visitChangevariableby,  # tested
    opcodes.DATA_SHOW_VARIABLE: data.visitShowvariable,  # tested
    opcodes.DATA_HIDE_VARIABLE: data.visitHidevariable,  # tested

    # TODO: While writing tests I noticed, that the pen blocks changed a bit now,
    # TODO: check if the conversion of those blocks is still correct / necessary.
    #### pen blocks ####
    opcodes.PEN_CLEAR: pen.visitClear,  # tested
    opcodes.PEN_STAMP: pen.visitStamp,  # tested
    opcodes.PEN_DOWN: pen.visitPenDown,  # tested
    opcodes.PEN_UP: pen.visitPenUp,  # tested
    opcodes.PEN_SET_COLOR: pen.visitSetPenColorToColor,  # tested
    opcodes.PEN_CHANGE_COLOR: pen.visitChangePenColorParamBy,  # tested
    opcodes.PEN_COLOR_PARAM_MENU: pen.visitPen_menu_colorParam,  # tested
    opcodes.PEN_SET_PARAM: pen.visitSetPenColorParamTo,  # tested
    opcodes.PEN_CHANGE_SIZE: pen.visitChangePenSizeBy,  # tested
    opcodes.PEN_SET_SIZE: pen.visitSetPenSizeTo,  # tested
    opcodes.PEN_SET_SHADE_TO_NUMBER: pen.visitSetPenShadeToNumber,  # tested
    opcodes.PEN_CHANGE_PEN_SHADE_BY: pen.visitChangePenShadeByNumber,  # tested
    opcodes.PEN_SET_PEN_HUE_TO_NUMBER: pen.visitSetPenHueToNumber,  # tested
}
