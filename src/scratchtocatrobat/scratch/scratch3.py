from scratchtocatrobat.tools import logger, helpers
import os
import json

log = logger.log

def get_block_attribute(block, key):
    if key in block.keys():
        return block[key]
    return None


class Scratch3Block(object):

    def __init__(self, block, name):
        self.name = name
        self.opcode = get_block_attribute(block, "opcode")
        self.nextName = get_block_attribute(block, "next")
        self.parentName = get_block_attribute(block, "parent")
        self.nextBlock = None
        self.parentBlock = None
        self.inputs = get_block_attribute(block, "inputs")
        self.fields = get_block_attribute(block, "fields")
        self.topLevel = get_block_attribute(block, "topLevel")
        self.shadow = get_block_attribute(block, "shadow")
        self.mutation = get_block_attribute(block, "mutation")
        self.x = 0
        self.y = 0
        if self.topLevel:
            self.x = block["x"]
            self.y = block["y"]

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
        stageSprite["info"] = self.raw_dict["meta"]
        stageSprite["penLayerMD5"] = "Scratch3Doesn'tHaveThis"
        stageSprite["penLayerID"] = 0 #TODO: this doesn't exist in scratch3 what is this!?
        stageSprite["tempoBPM"] = 60
        stageSprite["videoAlpha"] = 0.5
        return stageSprite

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

        #TODO: check if list is global, if it is add it to the list list of the stage, same for variables
        lists = []
        for list in sprite["lists"].values():
            curlist = {}
            curlist["listName"] = list[0]
            curlist["contents"] = list[1]
            curlist["isPersistent"] = list[2] if len(list) > 2 else False
            curlist["x"] = 1
            curlist["y"] = 1
            curlist["width"] = 1
            curlist["height"] = 1
            curlist["visible"] = True
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
        i = 0
        for s3Sound in sprite["sounds"]:
            i += 1
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
            # scratch2ProjectDict["indexInLibrary"] = sprite["indexInLibrary"]
            # scratch2ProjectDict["spriteInfo"] = sprite["spriteInfo"]
            scratch2ProjectDict["visible"] = sprite["visible"]

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
            project_dict = json.load(json_file)
            if "targets" in project_dict.keys():
                return True
            else:
                return False

def convert_to_scratch2_data(scratch_project_dir):
    parser = Scratch3Parser(os.path.join(scratch_project_dir, helpers.config.get("SCRATCH", "code_file_name")), scratch_project_dir)
    scratch2Data = parser.parse_sprites()
    with open(os.path.join(scratch_project_dir, helpers.config.get("SCRATCH", "code_file_name")), 'w') as json_file:
        json_file.flush()
        json.dump(scratch2Data, json_file, sort_keys=True, indent=4, separators=(',', ': '))
