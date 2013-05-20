import org.catrobat.catroid.content as catbase
import org.catrobat.catroid.content.bricks as catbricks
from scratchtobat import common, sb2

# based on: http://code.google.com/p/sb2-js/source/browse/trunk/editor.htm
SCRATCH_TO_CATROBAT_MAPPING = {
    # keys with value=None will be converted to WaitBrick with 500 ms
    "whenGreenFlag": catbase.StartScript,
    "whenIReceive": None,
    "whenKeyPressed": catbase.BroadcastScript,
    "whenSensorGreaterThan": None,
    "whenSceneStarts": None,
    
    "broadcast:": None,
    "doReturn": None,
    "doWaitUntil": None,
    "wait:elapsed:from:": None,
    "stopAll": None,
    
    # conditionals
    "doForever": catbricks.ForeverBrick,
    "doIf": None,
    "doIfElse": None,
    "doRepeat": catbricks.RepeatBrick,
    "doUntil": None,
    
    "turnRight:": None,
    "turnLeft:": None,
    "heading:": None,
    "forward:": catbricks.MoveNStepsBrick,
    "pointTowards:": None,
    "gotoX:y:": None,
    "xpos:": None,
    "ypos:": None,
    "glideSecs:toX:y:elapsed:from:": None,
    "changeXposBy:": None,
    "changeYposBy:": None,
    
    # variables
    "setVar:to:": None,
    "changeVar:by:": None,
    "showVariable:": None,
    "hideVariable:": None,
    
    # lists
    "append:toList:": None,
    "deleteLine:ofList:": None,
    "insert:at:ofList:": None,
    "setLine:ofList:to:": None,
    
    # pen
    "clearPenTrails": None,
    "putPenDown": None,
    "putPenUp": None,
    "penColor:": None,
    "changePenHueBy:": None,
    "setPenHueTo:": None,
    "changePenShadeBy:": None,
    "setPenShadeTo:": None,
    "penSize:": None,
    "stampCostume": None,
    
    # looks
    "lookLike:": None,
    "nextCostume": None,
    "say:duration:elapsed:from:": None,
    "say:": None,
    "think:duration:elapsed:from:": None,
    "think:": None,
    "changeGraphicEffect:by:": None,
    "setGraphicEffect:to:": None,
    "filterReset": None,
    "changeSizeBy:": None,
    "setSizeTo:": None,
    "show": None,
    "hide": None,
    "comeToFront": None,
    "goBackByLayers:": None,
    
    # sound
    "playSound:": None,
    "doPlaySoundAndWait": None,
    "stopAllSounds": None,
    "rest:elapsed:from:": None,
    "noteOn:duration:elapsed:from:": None,
    "setVolumeTo:": None,
    "changeTempoBy:": None,
    "setTempoTo:": None,
    
    # midi
    "playDrum": None,
    
    # sensing
    "doAsk": None,
    "timerReset"
    
    ###############################
    # reporter blocks
    ################################
    "+": None,
    "-": None,
    "*": None,
    "\/": None,
    "randomFrom:to:": None,
    "<": None,
    "=": None,
    ">": None,
    "&": None,
    "|": None,
    "not": None,
    "concatenate:with:": None,
    "letter:of:": None,
    "stringLength:": None,
    "\\\\": None,
    "rounded": None,
    "computeFunction:of:": None,
    
    # variables
    "readVariable": None,
    
    # lists
    "getLine:ofList:": None,
    "lineCountOfList:": None,
    "list:contains:": None,
    
    # sensing
    "touching:": None,
    "touchingColor:": None,
    "color:sees:": None,
    "answer": None,
    "mouseX": None,
    "mouseY": None,
    "mousePressed": None,
    "keyPressed:": None,
    "distanceTo:": None,
    "timer": None,
    "getAttribute:of:": None,
    
    # motion
    "xpos": None,
    "ypos": None,
    "heading": None,
    
    # looks
    "costumeIndex": None,
    "scale": None,
}


# def convert_to_catrobat_bricks(brick):
#     if not isinstance(brick, list):
#         raise common.ScratchtobatError("Input must be list: {}".format(brick))
#     return SCRATCH_TO_CATROBAT_MAPPING[brick[0]]()

_DEFAULT_BRICK_CLASS = catbricks.WaitBrick


def _get_catrobat_class(sb2name):
    if not isinstance(sb2name, (str, unicode)):
        raise common.ScratchtobatError("Must be string: {}".format(sb2name)) 
    assert sb2name in SCRATCH_TO_CATROBAT_MAPPING, "Missing mapping for: " + sb2name
    java_class = SCRATCH_TO_CATROBAT_MAPPING.get(sb2name)
    if not java_class:
        if sb2name in sb2.SCRATCH_SCRIPTS:
            assert False, "Missing script mapping for: " + sb2name
        common.log.warning("No mapping for={}, using default class={}".format(sb2name, _DEFAULT_BRICK_CLASS))
        java_class = lambda *args: _DEFAULT_BRICK_CLASS(args[0], 500)
    return java_class


def _convert_script(sb2script_name, sprite):
    return _get_catrobat_class(sb2script_name)(sprite)


def convert_to_catrobat_project(sb2_project):
    catr_project = catbase.Project(None, sb2_project.name)
    for _ in sb2_project.objects:
        catr_sprite = convert_to_catrobat_sprite(_)
        catr_project.addSprite(catr_sprite)
    return catr_project


def convert_to_catrobat_sprite(sb2_obj):
    if not isinstance(sb2_obj, sb2.Object):
        raise common.ScratchtobatError("Input must be of type={}, but is={}".format(sb2.Object, type(sb2_obj)))
    sprite = catbase.Sprite(sb2_obj.get_objName())
    for sb2_script in sb2_obj.scripts:
        sprite.addScript(convert_to_catrobat_script(sb2_script, sprite))
    return sprite


def convert_to_catrobat_script(sb2_script, sprite):
    if not isinstance(sb2_script, sb2.Script) or not isinstance(sprite, catbase.Sprite):
        raise common.ScratchtobatError("Args must be of type={}, but are={}".format((sb2.Script, catbase.Sprite), (type(sb2_script), type(sprite))))
    cat_script = _convert_script(sb2_script.script_id, sprite)
    for sb2_brick in sb2_script.script_bricks:
        cat_bricks = convert_to_catrobat_bricks(sb2_brick, sprite)
        for brick in cat_bricks:
            cat_script.addBrick(brick)
    return cat_script


def convert_to_catrobat_bricks(sb2_brick, cat_sprite):
    if not sb2_brick or not (isinstance(sb2_brick, list) and isinstance(sb2_brick[0], (str, unicode))):
        raise common.ScratchtobatError("Wrong input, must be list with string as first element: {}".format(sb2_brick))
    common.log.debug("Brick to convert={}".format(sb2_brick))
    brick_name = sb2_brick[0]
    brick_arguments = sb2_brick[1:]
    catr_bricks = []
    try:
        if brick_name in {'doRepeat', 'doForever'}:
            if brick_name == 'doRepeat':
                times_value, nested_bricks = brick_arguments
                catr_loop_start_brick = _get_catrobat_class(brick_name)(cat_sprite, times_value)
            elif brick_name == 'doForever':
                nested_bricks = brick_arguments[0]
                catr_loop_start_brick = _get_catrobat_class(brick_name)(cat_sprite)
            else:
                assert False, "Missing conditional branch for: " + brick_name
            catr_bricks += [catr_loop_start_brick]
            for brick_arg in nested_bricks:
                catr_bricks += convert_to_catrobat_bricks(brick_arg, cat_sprite)
            catr_bricks += [catbricks.LoopEndBrick(cat_sprite, catr_loop_start_brick)]
            
        else:
            common.log.info("Get mapping for {} in {}".format(brick_name, cat_sprite))
            catr_bricks += [_get_catrobat_class(brick_name)(cat_sprite, *brick_arguments)]
    except TypeError as e:
        common.log.exception(e)
        assert False, "Non-matching arguments: {}".format(brick_arguments)
    return catr_bricks
