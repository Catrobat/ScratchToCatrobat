import looks, motion, event, sensing, sound, operator, control, data, pen

visitormap = {
    ### event blocks ####
    "FLAG_CLICKED": event.visitWhenflagclicked,  # tested
    "BROADCAST": event.visitBroadcast,  # tested
    "BROADCAST_AND_WAIT": event.visitBroadcastandwait,  # tested
    "KEY_PRESSED": event.visitWhenkeypressed,  # tested
    "SPRITE_CLICKED": event.visitWhenthisspriteclicked,  # tested
    "GREATER_THAN": event.visitWhengreaterthan,  # tested
    "BACKDROP_SWITCHED_TO": event.visitWhenbackdropswitchesto,  # tested
    "BROADCAST_RECEIVED": event.visitWhenbroadcastreceived,  # tested

    ### motion blocks ####
    "MOTION_MOVE_STEPS": motion.visitMovesteps,  # tested
    "MOTION_TURN_RIGHT": motion.visitTurnright,  # tested
    "MOTION_TURN_LEFT": motion.visitTurnleft,  # tested
    "MOTION_GOTO": motion.visitGoto,  # tested
    "MOTION_GOTO_XY": motion.visitGotoxy,  # tested
    "MOTION_GLIDE_TO": motion.visitGlideto,  # tested
    "MOTION_GLIDE_SECS_TO_XY": motion.visitGlidesecstoxy,  # tested
    "MOTION_POINT_IN_DIR": motion.visitPointindirection,  # tested
    "MOTION_POINT_TOWARDS": motion.visitPointtowards,  # tested
    "MOTION_CHANGE_BY_XY": motion.visitChangexby,  # tested
    "MOTION_SET_X": motion.visitSetx,  # tested
    "MOTION_CHANGE_Y_BY": motion.visitChangeyby,  # tested
    "MOTION_SET_Y": motion.visitSety,  # tested
    "MOTION_BOUNCE_OFF_EDGE": motion.visitIfonedgebounce,  # tested
    "MOTION_SET_ROTATIONSTYLE": motion.visitSetrotationstyle,  # tested
    "MOTION_GOTO_MENU": motion.visitGoto_menu,  # tested
    "MOTION_GLIDE_TO_MENU": motion.visitGlideto_menu,  # tested
    "MOTION_POINT_TOWARDS_MENU": motion.visitPointtowards_menu,  # tested
    "MOTION_DIR": motion.visitDirection,  # tested
    "MOTION_Y_POS": motion.visitYposition,  # tested
    "MOTION_X_POS": motion.visitXposition,  # tested

    ### look blocks ####
    "LOOKS_SAY_FOR_SECS": looks.visitSayforsecs,  # tested
    "LOOKS_SAY": looks.visitSay,  # tested
    "LOOKS_THINK_FOR_SECS": looks.visitThinkforsecs,  # tested
    "LOOKS_THINK": looks.visitThink,  # tested
    "LOOKS_SWITCH_COSTUME_TO": looks.visitSwitchcostumeto,  # tested
    "LOOKS_NEXT_COSTUME": looks.visitNextcostume,  # tested
    "LOOKS_SWITCH_BACKDROP_TO": looks.visitSwitchbackdropto,  # tested
    "LOOKS_NEXT_BACKDROP": looks.visitNextbackdrop,  # tested
    "LOOKS_CHANGE_SIZE_BY": looks.visitChangesizeby,  # tested
    "LOOKS_SET_SIZE_TO": looks.visitSetsizeto,  # tested
    "LOOKS_CHANGE_EFFECT_BY": looks.visitChangeeffectby,  # tested
    "LOOKS_SET_EFFECT_TO": looks.visitSeteffectto,  # tested
    "LOOKS_CLEAR_EFFECTS": looks.visitCleargraphiceffects,  # tested
    "LOOKS_SHOW": looks.visitShow,  # tested
    "LOOKS_HIDE": looks.visitHide,  # tested
    "LOOKS_GOTO_FRONT_BACK": looks.visitGotofrontback,  # tested
    "LOOKS_FORWARD_BACKWARD_LAYERS": looks.visitGoforwardbackwardlayers,  # tested by fleischhacker
    "LOOKS_COSTUME": looks.visitCostume,  # tested
    "LOOKS_BACKDROPS": looks.visitBackdrops,  # tested
    "LOOKS_COSTUME_NUMBER_NAME": looks.visitCostumenumbername,  # tested
    "LOOKS_SIZE": looks.visitSize,  # tested
    "looks_backdropnumbername": looks.visitBackdropnumbername,

    ### sound blocks ####
    "SOUNDS_PLAY": sound.visitPlay,  # tested
    "SOUNDS_PLAY_UNTIL_DONE": sound.visitPlayuntildone,  # tested
    "SOUNDS_STOP_ALL": sound.visitStopallsounds,  # tested
    "sound_changeeffectby": sound.visitChangeeffectby,  # TODO not implemented in catrobat yet
    "sound_seteffectto": sound.visitSeteffectto,  # TODO not implemented in catrobat yet
    "sound_cleareffects": sound.visitCleareffects,  # TODO not implemented in scratch2, workaroundq
    "SOUNDS_CHANGE_VOLUME_BY": sound.visitChangevolumeby,  # tested
    "SOUNDS_SET_VOLUME_TO": sound.visitSetvolumeto,  # tested
    "SOUNDS_MENU": sound.visitSounds_menu,  # tested
    "SOUNDS_VOLUME": sound.visitVolume,  # tested

    ### control blocks ####
    "CONTROL_WAIT": control.visitWait,  # tested
    "CONTROL_REPEAT": control.visitRepeat,  # tested
    "CONTROL_IF": control.visitIf,  # tested
    "CONTROL_IF_ELSE": control.visitIf_else,  # tested
    "CONTROL_WAIT_UNTIL": control.visitWait_until,  # tested
    "CONTROL_REPEAT_UNTIL": control.visitRepeat_until,  # tested
    "CONTROL_CREATE_CLONE_OF": control.visitCreate_clone_of,  # tested
    "CONTROL_CREATE_CLONE_OF_MENU": control.visitCreate_clone_of_menu,  # tested
    "CONTROL_STOP": control.visitStop,  # tested
    "CONTROL_START_AS_CLONE": control.visitStart_as_clone,  # tested
    "CONTROL_FOREVER": control.visitForever,  # tested
    "CONTROL_DELETE_THIS_CLONE": control.visitDelete_this_clone,  # tested
    "CONTROL_PROCEDURES_CALL": control.visitProcedures_call,  # tested
    "CONTROL_PROCEDURES_DEFINITION": control.visitProcedures_definition,  # tested
    "CONTROL_ARGUMENT_REPORTER_STRING": control.visitArgumentIntOrString,  # tested
    "CONTROL_ARGUMENT_REPORTER_BOOL": control.visitArgumentBool,  # tested
    "CONTROL_PROCEDURES_PROTOTYPE": control.visitProcedures_prototype,  # tested

    ### sensing blocks ####
    "SENSING_ASK_AND_WAIT": sensing.visitAskandwait,  # tested
    "SENSING_SET_DRAG_MODE": sensing.visitSetdragmode,  # tested
    "SENSING_RESET_TIMER": sensing.visitResettimer,  # tested
    "SENSING_DISTANCE_TO": sensing.visitDistanceto,  # tested
    "SENSING_TO_DISTANCE_MENU": sensing.visitDistanceto_menu,  # tested
    "SENSING_LOUDNESS": sensing.visitLoudness,  # tested
    "SENSING_COLOR_TOUCHING_COLOR": sensing.visitColoristouchingcolor,  # tested
    "SENSING_OF": sensing.visitOf,  # tested
    "SENSING_CURRENT": sensing.visitCurrent,  # tested
    "SENSING_ANSWER": sensing.visitAnswer,  # tested
    "SENSING_DAYS_SINCE_2000": sensing.visitDayssince2000,  # tested
    "SENSING_KEYPRESSED": sensing.visitKeypressed,  # tested
    "SENSING_KEY_OPTIONS": sensing.visitKey_options,
    "SENSING_MOUSEX": sensing.visitMousex,  # tested
    "SENSING_MOUSE_DOWN": sensing.visitMousedown,  # tested
    "SENSING_MOUSEY": sensing.visitMousey,  # tested
    "SENSING_TIMER": sensing.visitTimer,  # tested
    "SENSING_TOUCHING_COLOR": sensing.visitTouchingcolor,  # tested
    "SENSING_TOUCHING_OBJECT": sensing.visitTouchingObject,  # tested
    "SENSING_CURRENT_MENU": sensing.visitCurrent_menu,  # tested
    "SENSING_TOUCHING_OBJECT_MENU": sensing.visitTouchingObjectMenu,  # tested
    "SENSING_USERNAME": sensing.visitUsername,  # tested
    "SENSING_OF_OBJECT_MENU": sensing.visitOf_object_menu,  # tested

    ### operator blocks ####
    "OPERATOR_SUBSTRACT": operator.visitSubtract,  # tested
    "OPERATOR_GREATER": operator.visitGt,  # tested
    "OPERATOR_JOIN": operator.visitJoin,  # tested
    "OPERATOR_LETTER_OF": operator.visitLetter_of,  # tested
    "OPERATOR_LESS_THAN": operator.visitLt,  # tested
    "OPERATOR_NOT": operator.visitNot,  # tested
    "OPERATOR_MODULO": operator.visitMod,  # tested
    "OPERATOR_ADD": operator.visitAdd,  # tested
    "OPERATOR_EQUALS": operator.visitEquals,  # tested
    "OPERATOR_MATH_OP": operator.visitMathop,  # tested
    "OPERATOR_AND": operator.visitAnd,  # tested
    "OPERATOR_ROUND": operator.visitRound,  # tested
    "OPERATOR_MULTIPLY": operator.visitMultiply,  # tested
    "OPERATOR_RANDOM": operator.visitRandom,  # tested
    "OPERATOR_DIVIDE": operator.visitDivide,  # tested
    "OPERATOR_CONTAINS": operator.visitContains,  # tested
    "OPERATOR_OR": operator.visitOr,  # tested
    "OPERATOR_LENGTH": operator.visitLength,  # tested

    ### data blocks ####
    "DATA_ADD_TO_LIST": data.visitAddtolist,  # tested
    "DATA_DELETE_OF_LIST": data.visitDeleteoflist,  # tested
    "DATA_INSERT_AT_LIST": data.visitInsertatlist,  # tested
    "DATA_REPLACE_ITEM_OF_LIST": data.visitReplaceitemoflist,  # tested
    "DATA_ITEM_OF_LIST": data.visitItemoflist,  # tested
    "DATA_ITEMNUM_OF_LIST": data.visitItemnumoflist,  # tested
    "DATA_LENGTH_OF_LIST": data.visitLengthoflist,  # tested
    "DATA_LIST_CONTAINS_ITEM": data.visitListcontainsitem,  # tested
    "DATA_SHOW_LIST": data.visitShowlist,  # tested
    "DATA_HIDE_LIST": data.visitHidelist,  # tested
    "DATA_CONTENTS_OF_LIST": data.visitContentsoflist,  # tested
    "DATA_SET_VARIABLE_TO": data.visitSetvariableto,  # tested
    "DATA_CHANGE_VARIABLE_BY": data.visitChangevariableby,  # tested
    "DATA_SHOW_VARIABLE": data.visitShowvariable,  # tested
    "DATA_HIDE_VARIABLE": data.visitHidevariable,  # tested

    # TODO: While writing tests I noticed, that the pen blocks changed a bit now,
    # TODO: check if the conversion of those blocks is still correct / necessary.
    #### pen blocks ####
    "PEN_CLEAR": pen.visitClear,  # tested
    "PEN_STAMP": pen.visitStamp,  # tested
    "PEN_DOWN": pen.visitPenDown,  # tested
    "PEN_UP": pen.visitPenUp,  # tested
    "PEN_SET_COLOR": pen.visitSetPenColorToColor,  # tested
    "PEN_CHANGE_COLOR": pen.visitChangePenColorParamBy,  # tested
    "PEN_COLOR_PARAM_MENU": pen.visitPen_menu_colorParam,  # tested
    "PEN_SET_PARAM": pen.visitSetPenColorParamTo,  # tested
    "PEN_CHANGE_SIZE": pen.visitChangePenSizeBy,  # tested
    "PEN_SET_SIZE": pen.visitSetPenSizeTo,  # tested
    "PEN_SET_SHADE_TO_NUMBER": pen.visitSetPenShadeToNumber,  # tested
    "PEN_CHANGE_PEN_SHADE_BY": pen.visitChangePenShadeByNumber,  # tested
    "PEN_SET_PEN_HUE_TO_NUMBER": pen.visitSetPenHueToNumber,  # tested
}
