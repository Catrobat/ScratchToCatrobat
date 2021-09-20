from scratchtocatrobat.tools import logger, helpers
import os
import json

log = logger.log

MONITOR_COLORS = {
    "motion":  5019647,#"rgb( 76,151,255)"
    "looks":  10053375,#"rgb(153,102,255)"
    "sound":  13591503,#"rgb(207, 99,207)"
    "sensing": 6074838,#"rgb( 92,177,214)"
    "data":   16747546,#"rgb(255,140, 26)"
}
MONITOR_MODE_MAPPING = {
    "default": 1,
    "large": 2,
    "slider": 3,
    "list": 4
}

def get_block_attribute(block, key):
    if key in block.keys():
        return block[key]
    return None

class Scratch3Block(object):

    def __init__(self, block, name):
        self.name = name
        self.opcode = block.get("opcode")
        self.nextName = block.get("next")
        self.parentName = block.get("parent")
        self.nextBlock = None
        self.parentBlock = None
        self.inputs = block.get("inputs")
        self.fields = block.get("fields")
        self.topLevel = block.get("topLevel")
        self.shadow = block.get("shadow")
        self.mutation = block.get("mutation")
        self.comment = block.get("comment")
        self.x = 0
        self.y = 0
        if self.topLevel:
            self.x = block.get("x")
            self.y = block.get("y")

class Scratch3Parser(object):
    scratch2dict = {}
    def fixBadScratch3Hashes(self, projectFile, scratch_project_dir):
        import glob
        import os
        from scratchtocatrobat.tools import common
        file_content = projectFile.read()
        for file in glob.glob(scratch_project_dir + "/*.*"):
            if not file.endswith(".json"):
                file_hash = common.md5_hash(file)
                newname = scratch_project_dir+"/"+ file_hash +"." +file.split(".")[-1]
                os.rename(file, newname)
                oldfile = "".join(file.split('/')[-1].split('.')[0:-1])
                file_content = file_content.replace(oldfile ,file_hash)
        projectFile.flush()
        projectFile.write(file_content)
        return file_content

    def __init__(self, file_path, scratch_project_dir):
        import json

        with open(file_path, "r+") as projectFile:
            new_json = self.fixBadScratch3Hashes(projectFile, scratch_project_dir)
            self.raw_dict = json.loads(new_json)

    def parse_sprites(self):
        sprites = self.raw_dict["targets"]
        scratch2Data = {}
        scratch2Data['sprites'] = []
        stageSprite = {}

        for sprite in sprites:
            spriteContent = self.parse_sprite(sprite)
            if sprite["isStage"]:
                stageSprite = spriteContent
            else:
                scratch2Data['sprites'].append(spriteContent)

        stageSprite["children"] = []
        for sprite in scratch2Data['sprites']:
            stageSprite["children"].append(sprite)
        for monitor in self.raw_dict["monitors"]:
            parsed_monitor = self.parse_monitor(monitor)
            if parsed_monitor:
                stageSprite["children"].append(parsed_monitor)

        stageSprite["info"] = self.raw_dict["meta"]
        stageSprite["penLayerMD5"] = "DummyValue-Scratch3Doesn'tHaveThis"
        stageSprite["penLayerID"] = -1
        stageSprite["tempoBPM"] = 60
        stageSprite["videoAlpha"] = 0.5
        return stageSprite

    @staticmethod
    def parse_monitor(monitor):
        assert "opcode" in monitor and "mode" in monitor and "params" in monitor and "x" in monitor and "y" in monitor
        MONITOR_CMD_MAPPING = {
            "sensing_answer": "answer",
            "looks_backdropnumber": "backgroundIndex",
            "looks_backdropname": "sceneName",
            "looks_costumenumbername": "costumeIndex",
            "data_variable": "getVar:",
            "motion_direction": "heading",
            "looks_size": "scale",
            "sensing_loudness": "soundLevel",
            "sensing_current": "timeAndDate",
            "sensing_timer": "timer",
            "sensing_username": "username",
            "sound_volume": "volume",
            "motion_xposition": "xpos",
            "motion_yposition": "ypos"
        }
        MONITOR_LABEL_MAPPING = {
            "sensing_answer": "answer",
            "looks_backdropnumber": "backdrop number",
            "looks_backdropname": "backdrop name",
            "looks_costumenumbername": "costume number",
            "motion_direction": "direction",
            "looks_size": "size",
            "sensing_loudness": "loudness",
            "sensing_timer": "timer",
            "sensing_username": "username",
            "sound_volume": "volume",
            "motion_xposition": "x position",
            "motion_yposition": "y position"
        }
        MONITOR_LABEL_CURRENT_MAPPING = {
            "YEAR": "year",
            "MONTH": "month",
            "DATE": "date",
            "DAYOFWEEK": "day of week",
            "HOUR": "hour",
            "MINUTE": "minute",
            "SECOND": "second"
        }
        MONITOR_PARAM_MAPPING = {
            "data_variable": lambda param: param["VARIABLE"],
            "sensing_current": lambda param: param["CURRENTMENU"]
        }
        if not monitor["mode"] in MONITOR_MODE_MAPPING:
            log.warn("Monitor with unknown mode will not be created.")
            return None
        #assert monitor["mode"] in MONITOR_MODE_MAPPING
        if monitor["mode"] == 'list':
            if not "LIST" in monitor["params"]:
                log.warn("Monitor with mode 'list' contains no parameter 'LIST' and will not be created.")
                return None
            #assert "LIST" in monitor["params"]
            scratch2_monitor = {
                "listName": monitor["params"]["LIST"],
                "contents": monitor.get("value", []),
                "isPersistent": monitor.get("isPersistent", False),
                "x": monitor["x"],
                "y": monitor["y"],
                "width": monitor["width"] if "width" in monitor and monitor["width"] != 0 else 100,
                "height": monitor["height"] if "height" in monitor and monitor["height"] != 0 else 200,
                "visible": monitor["visible"]
            }
        else:
            #sb3 has same opcode for background # and name, sb2 has two different opcodes => decide opcode depending on param
            if monitor["opcode"] == "looks_backdropnumbername":
                if monitor.get("params", {}).get("NUMBER_NAME") == "name":
                    monitor["opcode"] = "looks_backdropname"
                else:
                    monitor["opcode"] = "looks_backdropnumber"
            #assert monitor["opcode"] in MONITOR_CMD_MAPPING
            if not monitor["opcode"] in MONITOR_CMD_MAPPING:
                log.warn("Monitor with unknown opcode will not be created.")
                return None
            target = monitor.get("spriteName", None)
            param = (MONITOR_PARAM_MAPPING[monitor["opcode"]](monitor["params"]) if monitor["opcode"] in MONITOR_PARAM_MAPPING else None)
            if monitor["opcode"] == "sensing_current":
                label = MONITOR_LABEL_CURRENT_MAPPING[param]
            elif monitor["opcode"] == "data_variable":
                label = param
            else:
                label = MONITOR_LABEL_MAPPING[monitor["opcode"]]

            scratch2_monitor = {
                "cmd": MONITOR_CMD_MAPPING[monitor["opcode"]],
                "mode": MONITOR_MODE_MAPPING[monitor["mode"]],
                "isDiscrete": monitor.get("isDiscrete", True),
                "label": ((target + ": ") if target else "") + label,
                "param": param,
                "sliderMax": monitor.get("sliderMax", 100),
                "sliderMin": monitor.get("sliderMin", 0),
                "target": target,
                "visible": monitor["visible"],
                "x": monitor["x"],
                "y": monitor["y"],
            }
            for color_name, color_code in MONITOR_COLORS.items():
                if monitor["opcode"].startswith(color_name):
                    scratch2_monitor["color"] = color_code
                    break
            else:
                log.info("Can't find color for opcode " + monitor["opcode"] + ". Using black.")
                scratch2_monitor["color"] = 0
        return scratch2_monitor

    def parse_sprite(self, sprite):
        from scratch3visitor.visitorUtil import BlockContext, visitScriptBlock
        log.info("-" * 80)
        log.info("[Scratch3]  Converting Sprite: {}".format(sprite["name"]))

        script_blocks = []
        temp_block_dict = {}
        for block in sprite["blocks"]:
            try:
                temp_block_dict[block] = Scratch3Block(sprite["blocks"][block], block)
            except AttributeError as ex:
                log.warn("Block with id: " + block + " could not be parsed: " + ex.message)

        for blockId in temp_block_dict:
            self.build_block_structure(blockId, temp_block_dict)

        for blockId in temp_block_dict:
            if temp_block_dict[blockId].topLevel:
                script_blocks.append(temp_block_dict[blockId])
        scratch2ProjectDict = {}
        scratch2ProjectDict["scripts"] = []

        for block in script_blocks:
            blockcontext = BlockContext(block, temp_block_dict)
            scratch2ProjectDict["scripts"] += [[1,1, visitScriptBlock(blockcontext)]]
        variables = []
        for var in sprite["variables"].values():
            curvar = {}
            curvar["name"] = var[0]
            curvar["value"] = var[1]
            curvar["isPersistent"] = var[2] if len(var) > 2 else False
            variables.append(curvar)

        lists = []
        for id in sprite["lists"].keys():
            matching_raws = [m for m in self.raw_dict["monitors"] if m.get("id") == id]
            if len(matching_raws) == 0:
                log.warn("Monitor information is missing, this monitor will not be created.")
                continue
            curlist = self.parse_monitor(matching_raws[0])
            lists.append(curlist)
        scratch2ProjectDict["lists"] = lists

        scratch2ProjectDict["variables"] = variables
        scratch2ProjectDict["costumes"] = []
        for s3Costume in sprite["costumes"]:
            s2Costume = {}
            s2Costume["costumeName"] = s3Costume["name"]
            s2Costume["baseLayerID"] = s3Costume["assetId"]
            if "md5ext" in s3Costume:
                s2Costume["baseLayerMD5"] = s3Costume["md5ext"]
            else:
                s2Costume["baseLayerMD5"] = s3Costume["assetId"] + "." + s3Costume["dataFormat"]
            s2Costume["rotationCenterX"]= s3Costume["rotationCenterX"]
            s2Costume["rotationCenterY"]= s3Costume["rotationCenterY"]
            if "bitmapResolution" in s3Costume:
                s2Costume["bitmapResolution"] = s3Costume["bitmapResolution"]
            else:
                s2Costume["bitmapResolution"] =  1
            scratch2ProjectDict["costumes"].append(s2Costume)

        scratch2ProjectDict["sounds"] = []
        for i, s3Sound in enumerate(sprite["sounds"]):
            s2Sound = {}
            s2Sound["assetId"] =  s3Sound["assetId"]
            s2Sound["soundName"] =  s3Sound["name"]
            s2Sound["format"] =  s3Sound["dataFormat"]
            s2Sound["rate"] =  s3Sound["rate"]
            s2Sound["sampleCount"] =  s3Sound["sampleCount"]
            s2Sound["md5"] =  s3Sound["md5ext"]
            s2Sound["soundID"] = i #TODO this could be wrong
            scratch2ProjectDict["sounds"].append(s2Sound)

        scratch2ProjectDict["objName"] = sprite["name"]
        scratch2ProjectDict["currentCostumeIndex"] = sprite["currentCostume"]
        scratch2ProjectDict["isStage"] = sprite["isStage"]
        if not sprite['isStage']:
            scratch2ProjectDict["scratchX"] = sprite["x"]
            scratch2ProjectDict["scratchY"] = sprite["y"]
            scratch2ProjectDict["scale"] = sprite["size"] / 100.0
            scratch2ProjectDict["direction"] = sprite["direction"]
            scratch2ProjectDict["rotationStyle"] = sprite["rotationStyle"]
            scratch2ProjectDict["isDraggable"] = sprite["draggable"]
            scratch2ProjectDict["indexInLibrary"] = -sprite["layerOrder"] #layerOrder is reversed to indexInLayer
            # scratch2ProjectDict["spriteInfo"] = sprite["spriteInfo"]
            scratch2ProjectDict["visible"] = sprite["visible"]

        def _to_scratch2_comment(comment, offset):
            return [
                comment["x"],
                comment["y"],
                comment["width"],
                comment["height"],
                not comment["minimized"],
                offset,
                comment["text"]]


        #return a list of all input values. Adds values with keys SUBSTACK and SUBSTACK2 as last.
        def get_ordered_input_values(input_map):
            substack = None
            substack2 = None
            childs = []
            for name, value in input_map.iteritems():
                if name == "SUBSTACK":
                    substack = value
                elif name == "SUBSTACK2":
                    substack2 = value
                else:
                    childs.append(value)
            if substack:
                childs.append(substack)
            if substack2:
                childs.append(substack2)
            return childs

        def get_scratch2_comments_for_script(script_block, comments, offset=0):
            scratch2_comments = []
            block = script_block
            while block:
                if block.comment:
                    comment = comments.get(block.comment, None)
                    if comment:
                        scratch2_comments.append(_to_scratch2_comment(comment, offset))
                    else:
                        log.warn("Comment with ID: {} not found.".format(block.comment))
                offset += 1
                if block.inputs:
                    for sub_input_array in get_ordered_input_values(block.inputs):
                        if isinstance(sub_input_array[1], basestring):
                            sub_input = temp_block_dict.get(sub_input_array[1], None)
                            if sub_input and not sub_input.shadow:
                                child_scratch2_comments, offset = get_scratch2_comments_for_script(sub_input, comments, offset)
                                scratch2_comments.extend(child_scratch2_comments)
                block = block.nextBlock
            return scratch2_comments, offset

        def get_scratch2_comments(script_blocks, comments):
            offset = 0
            scratch2_comments = []
            for comment in comments.values():
                if not comment["blockId"]:
                    scratch2_comments.append(_to_scratch2_comment(comment, -1))
            for script_block in script_blocks:
                if script_block.opcode.startswith("event_"):
                    script_comments, offset = get_scratch2_comments_for_script(script_block, comments, offset)
                    scratch2_comments.extend(script_comments)
            return scratch2_comments

        scratch2ProjectDict["scriptComments"] = get_scratch2_comments(script_blocks, sprite["comments"])

        return scratch2ProjectDict

    def build_block_structure(self, blockId, temp_block_dict):
        try:
            block = temp_block_dict[blockId]
            if block.nextName is not None:
                block.nextBlock = temp_block_dict[block.nextName]
            if block.parentName is not None:
                block.parentBlock = temp_block_dict[block.parentName]
        except KeyError as ex:
            log.warn("Block: " + ex.message + " does not exist in the block dictionary.")

def is_scratch3_project(scratch_project_dir):
    if os.path.isfile(scratch_project_dir + '/' + helpers.config.get("SCRATCH", "code_file_name")):
        with open(os.path.join(scratch_project_dir, helpers.config.get("SCRATCH", "code_file_name")), 'r') as json_file:
            try:
                project_dict = json.load(json_file)
            except:
                # guess if is binary file, since Scratch 1.x saves project data in a binary file
                # instead of a JSON file like in 2.x
                textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
                is_binary_string = lambda bytesdata: bool(bytesdata.translate(None, textchars))
                json_file.seek(0, 0) # set file pointer back to the beginning of the file
                if is_binary_string(json_file.read(1024)): # check first 1024 bytes
                    raise EnvironmentError("Invalid JSON file. The project's code-file " \
                                           "seems to be a binary file. Project might be very old " \
                                           "Scratch project. Scratch projects lower than 2.0 are " \
                                           "not supported!")
                else:
                    raise EnvironmentError("Invalid JSON file. But the project's " \
                                           "code-file seems to be no binary file...")
            if "targets" in project_dict.keys():
                return True
            else:
                return False

def convert_to_scratch2_data(scratch_project_dir, project_id):
    parser = Scratch3Parser(os.path.join(scratch_project_dir, helpers.config.get("SCRATCH", "code_file_name")), scratch_project_dir)
    scratch2Data = parser.parse_sprites()
    assert "info" in scratch2Data
    assert "projectID" not in scratch2Data["info"]
    scratch2Data["info"]["projectID"] = project_id
    with open(os.path.join(scratch_project_dir, helpers.config.get("SCRATCH", "code_file_name")), 'w') as json_file:
        json_file.flush()
        json.dump(scratch2Data, json_file, sort_keys=True, indent=4, separators=(',', ': '))
