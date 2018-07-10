from scratchtocatrobat.scratch.scratch3 import Scratch3Block
from scratchtocatrobat.tools import logger

log = logger.log


def get_block(blockid, spriteblocks):
    if blockid in spriteblocks.keys():
        return spriteblocks[blockid]
    return blockid

def visitBlock(block):
    from blockmapping import visitormap

    if not isinstance(block, BlockContext):
        return block
    blocklist = []
    while block.block != None:
        subblock = visitormap.get(block.block.opcode, visitDefault)(block)
        blocklist.append(subblock)
        block = BlockContext(block.block.nextBlock, block.spriteblocks)
    if isinstance(blocklist[0], list) and len(blocklist) == 1:
        blocklist = blocklist[0]
    return blocklist

def visitScriptBlock(block):
    from blockmapping import visitormap

    if not isinstance(block, BlockContext):
        return block

    scriptblock = visitormap.get(block.block.opcode, visitDefault)(block)
    block = BlockContext(block.block.nextBlock, block.spriteblocks)
    blocklist = []
    blocklist.append(scriptblock)
    while block.block != None:
        subblock = visitormap.get(block.block.opcode, visitDefault)(block)
        blocklist.append(subblock)
        block = BlockContext(block.block.nextBlock, block.spriteblocks)
    return blocklist

def visitBlockList(blockcontext):
    from blockmapping import visitormap

    if not isinstance(blockcontext, BlockContext):
        return blockcontext
    blocklist = []

    while blockcontext.block != None:
        subblock = visitormap.get(blockcontext.block.opcode, visitDefault)(blockcontext)
        blocklist.append(subblock)
        blockcontext = BlockContext(blockcontext.block.nextBlock, blockcontext.spriteblocks)
    return blocklist

def visitLiteral(literal):
    if literal is None:
        return None #TODO: Warning or error message maybe?
    elif literal[0] == 12:
        return ["readVariable", literal[1]]
    elif literal[0] == 13:
        return ["contentsOfList:", literal[1]]
    elif literal[0] == 5 or literal[0] == 6 or literal[0] == 7:
        if literal[1] is None:
            return 0
        try:
            return int(literal[1])
        except:
            return str(literal[1])
    elif literal[0] == 4 or literal[0] == 8:
        if literal[1] == '':
            return 0.0
        return float(literal[1])
    elif literal[0] == 9:
        return literal[1]
    else:
        return literal[1]


def visitGeneric(blockcontext, attributename):
    block = blockcontext.block
    if attributename in block.inputs:
        substackstartblock = get_block(block.inputs[attributename][1], blockcontext.spriteblocks)
        if isinstance(substackstartblock, Scratch3Block):
            blocklist = visitBlock(BlockContext(substackstartblock, blockcontext.spriteblocks))
            if block.inputs[attributename][0] == 1:
                return blocklist[0]
            return blocklist
        return visitLiteral(block.inputs[attributename][1])
    return [False]

def visitDefault(blockcontext):
    log.warn("block not yet implemented: " + blockcontext.block.opcode)
    return ["say:", "ERROR: BLOCK NOT FOUND: " + blockcontext.block.opcode]

def visitCondition(blockcontext):
    block = blockcontext.block
    if "CONDITION" in block.inputs:
        conditionblock = get_block(block.inputs["CONDITION"][1], blockcontext.spriteblocks)
        if isinstance(conditionblock, Scratch3Block):
            condition = visitGeneric(blockcontext, "CONDITION")
            return condition
    return False

def visitSubstack(blockcontext, substackkey):
    if substackkey in blockcontext.block.inputs:
        substackstartblock = get_block(blockcontext.block.inputs[substackkey][1], blockcontext.spriteblocks)
        if isinstance(substackstartblock, Scratch3Block):
            substack = visitBlockList(BlockContext(substackstartblock, blockcontext.spriteblocks))
            return substack
    return None

def visitMutation(blockcontext):
    return blockcontext.block.mutation["proccode"]

def visitParams(blockcontext):
    paramids = blockcontext.block.mutation["argumentids"].strip("[]").split(",")
    sanitized = []
    for paramid in paramids:
        sanitized.append(paramid.strip("\""))
    arguments = []

    for paramid in sanitized:
        if paramid == "":
            continue
        arg = visitGeneric(blockcontext, paramid)
        arguments.append(arg)
    return arguments

def sanitizeListArgument(listString):
    paramids = listString.strip("[]").split(",")
    sanitized = []
    for paramid in paramids:
        paramid = paramid.strip("\"")
        if paramid == '':
            continue
        sanitized.append(paramid)
    return sanitized

def sanitizeListDefault(listString):
    paramids = listString.strip("[]").split(",")
    sanitized = []
    for paramid in paramids:
        paramid = paramid.strip("\"")
        if paramid == 'true': paramid = True
        if paramid == 'false': paramid = False
        if paramid == 'todo': paramid = None #TODO: this is most likely only a temporary placeholder
        sanitized.append(paramid)
    return sanitized




class BlockContext(object):
    def __init__(self, block, spriteblocks):
        self.block = block
        self.spriteblocks = spriteblocks