import looks, motion, event, sensing, sound, operator, control, data, pen, music
from scratchtocatrobat.scratch.scratch3visitor.scratch2_json_format import Scratch3_2Opcodes as opcodes

visitormap = {
    ### event blocks ####
    "event_whenflagclicked" : event.visitWhenflagclicked, #tested
    "event_broadcast" : event.visitBroadcast, #tested
    "event_broadcastandwait" : event.visitBroadcastandwait, #tested
    "event_whenkeypressed" : event.visitWhenkeypressed, #tested
    "event_whenthisspriteclicked" : event.visitWhenthisspriteclicked, #tested
    "event_whengreaterthan" : event.visitWhengreaterthan, #tested
    "event_whenbackdropswitchesto" : event.visitWhenbackdropswitchesto, #tested
    "event_whenbroadcastreceived" : event.visitWhenbroadcastreceived, #tested

    ### motion blocks ####
    "motion_movesteps" : motion.visitMovesteps, #tested
    "motion_turnright" : motion.visitTurnright, #tested
    "motion_turnleft" : motion.visitTurnleft,#tested
    "motion_goto" : motion.visitGoto,#tested
    "motion_gotoxy" : motion.visitGotoxy,#tested
    "motion_glideto" : motion.visitGlideto,#tested
    "motion_glidesecstoxy" : motion.visitGlidesecstoxy,#tested
    "motion_pointindirection" : motion.visitPointindirection,#tested
    "motion_pointtowards" : motion.visitPointtowards,#tested
    "motion_changexby" : motion.visitChangexby,#tested
    "motion_setx" : motion.visitSetx,#tested
    "motion_changeyby" : motion.visitChangeyby,#tested
    "motion_sety" : motion.visitSety,#tested
    "motion_ifonedgebounce" : motion.visitIfonedgebounce,#tested
    "motion_setrotationstyle" : motion.visitSetrotationstyle,#tested
    "motion_goto_menu" : motion.visitGoto_menu,#tested
    "motion_glideto_menu" : motion.visitGlideto_menu,#tested
    "motion_pointtowards_menu" : motion.visitPointtowards_menu,#tested
    "motion_direction" : motion.visitDirection,#tested
    "motion_yposition" : motion.visitYposition,#tested
    "motion_xposition" : motion.visitXposition,#tested

    ### look blocks ####
    "looks_sayforsecs" : looks.visitSayforsecs,#tested
    "looks_say" : looks.visitSay,#tested
    "looks_thinkforsecs" : looks.visitThinkforsecs,#tested
    "looks_think" : looks.visitThink,#tested
    "looks_switchcostumeto" : looks.visitSwitchcostumeto,#tested
    "looks_nextcostume" : looks.visitNextcostume,#tested
    "looks_switchbackdropto" : looks.visitSwitchbackdropto,#tested
    "looks_nextbackdrop" : looks.visitNextbackdrop,#tested
    "looks_changesizeby" : looks.visitChangesizeby,#tested
    "looks_setsizeto" : looks.visitSetsizeto,#tested
    "looks_changeeffectby" : looks.visitChangeeffectby,#tested
    "looks_seteffectto" : looks.visitSeteffectto,#tested
    "looks_cleargraphiceffects" : looks.visitCleargraphiceffects,#tested
    "looks_show" : looks.visitShow,#tested
    "looks_hide" : looks.visitHide,#tested
    "looks_gotofrontback" : looks.visitGotofrontback,#tested
    "looks_goforwardbackwardlayers" : looks.visitGoforwardbackwardlayers, #tested by fleischhacker
    "looks_costume" : looks.visitCostume, #tested
    "looks_backdrops" : looks.visitBackdrops, #tested
    "looks_costumenumbername" : looks.visitCostumenumbername, #tested
    "looks_size" : looks.visitSize,#tested
    "looks_backdropnumbername" : looks.visitBackdropnumbername,

    ### sound blocks ####
    "sound_play" : sound.visitPlay,#tested
    "sound_playuntildone" : sound.visitPlayuntildone,#tested
    "sound_stopallsounds" : sound.visitStopallsounds,#tested
    "sound_changeeffectby" : sound.visitChangeeffectby, # TODO not implemented in catrobat yet
    "sound_seteffectto" : sound.visitSeteffectto, # TODO not implemented in catrobat yet
    "sound_cleareffects" : sound.visitCleareffects, # TODO not implemented in scratch2, workaroundq
    "sound_changevolumeby" : sound.visitChangevolumeby,#tested
    "sound_setvolumeto" : sound.visitSetvolumeto,#tested
    "sound_sounds_menu" : sound.visitSounds_menu, #tested
    "sound_volume" : sound.visitVolume,#tested

    ### control blocks ####
    "control_wait" : control.visitWait,#tested
    "control_repeat" : control.visitRepeat,#tested
    "control_if" : control.visitIf,#tested
    "control_if_else" : control.visitIf_else,#tested
    "control_wait_until" : control.visitWait_until,#tested
    "control_repeat_until" : control.visitRepeat_until,#tested
    "control_create_clone_of" : control.visitCreate_clone_of,#tested
    "control_create_clone_of_menu" : control.visitCreate_clone_of_menu, #tested
    "control_stop" : control.visitStop,#tested
    "control_start_as_clone" : control.visitStart_as_clone,#tested
    "control_forever" : control.visitForever,#tested
    "control_delete_this_clone" : control.visitDelete_this_clone,#tested
    "procedures_call" : control.visitProcedures_call, #tested
    "procedures_definition" : control.visitProcedures_definition, #tested
    "argument_reporter_string_number" : control.visitArgumentIntOrString, #tested
    "argument_reporter_boolean" : control.visitArgumentBool, #tested
    "procedures_prototype" : control.visitProcedures_prototype, #tested

    ### sensing blocks ####
    "sensing_askandwait" : sensing.visitAskandwait,#tested
    "sensing_setdragmode" : sensing.visitSetdragmode,#tested
    "sensing_resettimer" : sensing.visitResettimer,#tested
    "sensing_distanceto" : sensing.visitDistanceto,#tested
    "sensing_distancetomenu" : sensing.visitDistanceto_menu, #tested
    "sensing_loudness" : sensing.visitLoudness,#tested
    "sensing_coloristouchingcolor" : sensing.visitColoristouchingcolor,#tested
    "sensing_of" : sensing.visitOf,#tested
    "sensing_current" : sensing.visitCurrent,#tested
    "sensing_answer" : sensing.visitAnswer,#tested
    "sensing_dayssince2000" : sensing.visitDayssince2000,#tested
    "sensing_keypressed" : sensing.visitKeypressed,#tested
    "sensing_keyoptions" : sensing.visitKey_options,
    "sensing_mousex" : sensing.visitMousex,#tested
    "sensing_mousedown" : sensing.visitMousedown,#tested
    "sensing_mousey" : sensing.visitMousey,#tested
    "sensing_timer" : sensing.visitTimer,#tested
    "sensing_touchingcolor" : sensing.visitTouchingcolor,#tested
    "sensing_touchingobject" : sensing.visitTouchingObject,#tested
    "sensing_currentmenu" : sensing.visitCurrent_menu, #tested
    "sensing_touchingobjectmenu" : sensing.visitTouchingObjectMenu,#tested
    "sensing_username" : sensing.visitUsername,#tested
    "sensing_of_object_menu" : sensing.visitOf_object_menu, #tested

    ### operator blocks ####
    "operator_subtract" : operator.visitSubtract,#tested
    "operator_gt" : operator.visitGt,#tested
    "operator_join" : operator.visitJoin,#tested
    "operator_letter_of" : operator.visitLetter_of,#tested
    "operator_lt" : operator.visitLt,#tested
    "operator_not" : operator.visitNot,#tested
    "operator_mod" : operator.visitMod,#tested
    "operator_add" : operator.visitAdd,#tested
    "operator_equals" : operator.visitEquals,#tested
    "operator_mathop" : operator.visitMathop,#tested
    "operator_and" : operator.visitAnd,#tested
    "operator_round" : operator.visitRound,#testedUSIC_PLAY_DRUM_FOR_BEATS
    "operator_multiply" : operator.visitMultiply,#tested
    "operator_random" : operator.visitRandom,#tested
    "operator_divide" : operator.visitDivide,#tested
    "operator_contains" : operator.visitContains,#tested
    "operator_or" : operator.visitOr,#tested
    "operator_length" : operator.visitLength,#tested

    ### data blocks ####
    "data_addtolist" : data.visitAddtolist,#tested
    "data_deleteoflist" : data.visitDeleteoflist,#tested
    "data_insertatlist" : data.visitInsertatlist,#tested
    "data_replaceitemoflist" : data.visitReplaceitemoflist,#tested
    "data_itemoflist" : data.visitItemoflist,#tested
    "data_itemnumoflist" : data.visitItemnumoflist,#tested
    "data_lengthoflist" : data.visitLengthoflist,#tested
    "data_listcontainsitem" : data.visitListcontainsitem,#tested
    "data_showlist" : data.visitShowlist,#tested
    "data_hidelist" : data.visitHidelist,#tested
    "data_contentsoflist" : data.visitContentsoflist,#tested
    "data_setvariableto" : data.visitSetvariableto,#tested
    "data_changevariableby" : data.visitChangevariableby,#tested
    "data_showvariable" : data.visitShowvariable,#tested
    "data_hidevariable" : data.visitHidevariable,#tested


    # TODO: While writing tests I noticed, that the pen blocks changed a bit now,
    # TODO: check if the conversion of those blocks is still correct / necessary.
    #### pen blocks ####
    "pen_clear" : pen.visitClear,#tested
    "pen_stamp" : pen.visitStamp,#tested
    "pen_penDown" : pen.visitPenDown,#tested
    "pen_penUp" : pen.visitPenUp,#tested
    "pen_setPenColorToColor" : pen.visitSetPenColorToColor,#tested
    "pen_changePenColorParamBy" : pen.visitChangePenColorParamBy,#tested
    "pen_menu_colorParam" : pen.visitPen_menu_colorParam, #tested
    "pen_setPenColorParamTo" : pen.visitSetPenColorParamTo, #tested
    "pen_changePenSizeBy" : pen.visitChangePenSizeBy,#tested
    "pen_setPenSizeTo" : pen.visitSetPenSizeTo,#tested
    "pen_setPenShadeToNumber" : pen.visitSetPenShadeToNumber, #tested
    "pen_changePenShadeBy" : pen.visitChangePenShadeByNumber, #tested
    "pen_setPenHueToNumber" : pen.visitSetPenHueToNumber, #tested

    opcodes.MUSIC_PLAY_DRUM_FOR_BEATS: music.visitPlayDrumForBeats,
    opcodes.MUSIC_MENU_DRUM: music.visitDrumMenu,
    opcodes.MUSIC_PLAY_NOTE_FOR_BEATS: music.visitPlayNoteForBeats,
    opcodes.NOTE: music.visitNoteMenu,
}

