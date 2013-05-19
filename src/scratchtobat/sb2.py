# based on: http://code.google.com/p/sb2-js/source/browse/trunk/editor.htm
from scratchtobat import common
import os
import json
SCRATCH_TO_CATROBAT_BRICK_MAPPING = {
    "whenGreenFlag": None,
    "stopAll": None,
    "whenIReceive": None,
    "doWaitUntil": None,
    "wait:elapsed:from:": None,
    "broadcast:": None,
    "doReturn": None,
    
    # conditionals
    "doForever": None,
    "doIf": None,
    "doIfElse": None,
    "doRepeat": None,
    "doUntil": None,
    
    "turnRight:": None,
    "turnLeft:": None,
    "heading:": None,
    "forward:": None,
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


class Project(object):
    _SCRATCH_PROJECT_DATA_FILE = "project.json"
    
    def __init__(self, project_path):
        if not os.path.isdir(project_path):
            raise ProjectError("Create project path: {}".format(project_path))
        self.json_path = os.path.join(project_path, self._SCRATCH_PROJECT_DATA_FILE)
        self.json_data = self.load_json_file(self.json_path)
        
    def load_json_file(self, json_file):
        if not os.path.exists(json_file):
            raise ProjectError("Provide project data file: {}".format(json_file))
        with open(json_file, "r") as fp:
            json_dict = json.load(fp)
            self.verify_scratch_json(json_dict)
            return json_dict
        
    def get_raw_data(self):
        return self.json_data
    
    def verify_scratch_json(self, json_dict):
        # FIXME: check which tags are really required
        for key in ["objName", "info", "currentCostumeIndex", "penLayerMD5", "tempoBPM", "videoAlpha", "children", "costumes", "sounds"]:
            if not key in json_dict:
                raise ProjectError("Key='{}' not found in {}".format(key, self.json_path))


class ProjectError(common.ScratchtobatError):
    pass


class Object(object):
    pass


class Script(object):
    
    def __init__(self, json_input):
        if not self.is_valid_script_input(json_input):
            raise ScriptError("Input is no valid Scratch sb2 json script.")
        self.script = json_input[2]

    @classmethod
    def is_valid_script_input(cls, json_input):
        return (isinstance(json_input, list) and len(json_input) == 3 and
            # NOTE: could use a json validator instead
            isinstance(json_input[0], int) and isinstance(json_input[1], int) and isinstance(json_input[2], list))
    
    def get_bricks(self):
        def get_bricks_recursively(nested_bricks):
            result = []
            common.log.info("{}".format(nested_bricks))
            for idx, brick in enumerate(nested_bricks):
                isBrickId = idx == 0 and isinstance(brick, str)
                isNestedBrick = isinstance(brick, list)
                if isBrickId:
                    common.log.debug("adding {}".format(brick))
                    assert brick in SCRATCH_TO_CATROBAT_BRICK_MAPPING, "Unknown brick id=" + brick
                    result += [brick]
                elif isNestedBrick:
                    common.log.debug("calling on {}".format(brick))
                    result += get_bricks_recursively(brick)
                else:
                    assert isinstance(brick, (int, str, float)), "Unhandled brick element type {} for {}".format(type(brick), brick)
                    continue
            return result
        
        return get_bricks_recursively(self.script)


class ScriptError(common.ScratchtobatError):
    pass
